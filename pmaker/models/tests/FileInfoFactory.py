#
# Copyright (C) 2011 Satoru SATOH <satoru.satoh @ gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.models.FileInfo import *  # *FileInfo and other classes
from pmaker.globals import *  # TYPE_*
from pmaker.utils import rm_rf

import os
import tempfile
import unittest



class TestFileInfoFactory(unittest.TestCase):

    def setUp(self):
        self.factory = FileInfoFactory()
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test__stat_normal(self):
        (mode, uid, gid) = self.factory._stat("/dev/null")
        self.assertNotEquals(mode, None)
        self.assertNotEquals(uid, None)
        self.assertNotEquals(gid, None)

    def test__stat_no_permission(self):
        if os.getuid() == 0:
            print >> sys.stderr, "You're root. Skip this test."
            return

        self.assertEquals(self.factory._stat("/root/.bashrc"), None)

    def test_create__file(self):
        path = os.path.join(self.workdir, "file.txt")
        open(path, "w").write("type file\n")
        fi = self.factory.create(path)

        self.assertTrue(isinstance(fi, FileInfo))
        self.assertEquals(fi.type(), TYPE_FILE)

    def test_create__dir(self):
        path = self.workdir
        fi = self.factory.create(path)

        self.assertTrue(isinstance(fi, DirInfo))
        self.assertEquals(fi.type(), TYPE_DIR)

    def test_create__symlink(self):
        src = os.path.join(self.workdir, "file.txt")
        path = os.path.join(self.workdir, "symlink.txt")
        open(src, "w").write("type file\n")
        os.symlink(src, path)
        fi = self.factory.create(path)

        self.assertTrue(isinstance(fi, SymlinkInfo))
        self.assertEquals(fi.type(), TYPE_SYMLINK)

    def test_create__other(self):
        path = os.path.join(self.workdir, "fifo.pipe")
        os.mkfifo(path)
        fi = self.factory.create(path)

        self.assertTrue(isinstance(fi, OtherInfo))
        self.assertEquals(fi.type(), TYPE_OTHER)

    def test_create__unknown(self):
        path = "/root/.bashrc"
        fi = self.factory.create(path)

        self.assertTrue(isinstance(fi, UnknownInfo))
        self.assertEquals(fi.type(), TYPE_UNKNOWN)


# vim: set sw=4 ts=4 expandtab:
