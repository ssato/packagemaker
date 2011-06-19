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
from pmaker.models.FileInfo import *  # *FileInfo and other classes
from pmaker.utils import rm_rf, checksum

import os
import tempfile
import unittest


NULL_DICT = dict()



class TestFileInfo(unittest.TestCase):

    def test__init__(self):
        path = "/etc/hosts"

        st = os.lstat(path)
        (mode, uid, gid) = (st.st_mode, st.st_uid, st.st_gid)
        csum = checksum(path)

        fi = FileInfo(path, mode, uid, gid, csum, NULL_DICT)
        self.assertTrue(isinstance(fi, FileInfo))


class TestDirInfo(unittest.TestCase):

    def test__init__(self):
        path = "/etc"

        st = os.lstat(path)
        (mode, uid, gid) = (st.st_mode, st.st_uid, st.st_gid)
        csum = checksum()

        fi = DirInfo(path, mode, uid, gid, csum, NULL_DICT)
        self.assertTrue(isinstance(fi, DirInfo))


class TestSymlinkInfo(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test__init__(self):
        path = os.path.join(self.workdir, "hosts")
        os.symlink("/etc/hosts", path)

        st = os.lstat(path)
        (mode, uid, gid) = (st.st_mode, st.st_uid, st.st_gid)
        csum = checksum(path)

        fi = SymlinkInfo(path, mode, uid, gid, csum, NULL_DICT)
        self.assertTrue(isinstance(fi, SymlinkInfo))

        self.assertFalse(fi.need_to_chmod())


# vim: set sw=4 ts=4 expandtab:
