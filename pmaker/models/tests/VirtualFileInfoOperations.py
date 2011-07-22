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
#
from pmaker.models.VirtualFileInfoOperations import *
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.models.FileInfo import *
from pmaker.utils import rm_rf

import os
import os.path
import tempfile
import unittest



class TestVirtualFileOperations(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.testfile1 = os.path.join(self.workdir, "test1.txt")
        os.system("touch " + self.testfile1)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_copy_main__w_content(self):
        fi = FileInfoFactory().create(self.testfile1)
        dest = self.testfile1 + ".2"

        content = open(fi.path, "rb").read()
        vfi = VirtualFileInfo(fi.path, fi.mode, fi.uid, fi.gid, fi.checksum, fi.xattrs, content=content)

        VirtualFileOperations.copy_main(vfi, dest, use_pyxattr=False)
        self.assertTrue(os.path.exists(dest))

    def test_copy_main__wo_content(self):
        fi = FileInfoFactory().create(self.testfile1)
        dest = self.testfile1 + ".2"

        path = fi.path + fi.checksum
        vfi = VirtualFileInfo(path, fi.mode, fi.uid, fi.gid, fi.checksum, fi.xattrs)

        VirtualFileOperations.copy_main(vfi, dest, use_pyxattr=False)
        self.assertTrue(os.path.exists(dest))



class TestVirtualDirOperations(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test_copy_main(self):
        path = os.path.join(self.workdir, "test0")
        os.makedirs(path)

        dest = os.path.join(self.workdir, "test1")
        fi = FileInfoFactory().create(path)

        vfi = VirtualDirInfo(fi.path, fi.mode, fi.uid, fi.gid, fi.checksum, fi.xattrs)

        VirtualDirOperations.copy_main(vfi, dest)
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.isdir(dest))



class TestVirtualSymlinkOperations(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        src = os.path.join(self.workdir, "test.txt")
        open(src, "w").write("test\n")

        self.path = os.path.join(self.workdir, "symlink.txt")
        os.symlink(src, self.path)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_copy_main(self):
        dest = os.path.join(self.workdir, "another_symlink.txt")
        fi = FileInfoFactory().create(self.path)

        vfi = VirtualSymlinkInfo(fi.path, fi.mode, fi.uid, fi.gid, fi.checksum, fi.xattrs)

        VirtualSymlinkOperations.copy_main(vfi, dest)
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.islink(dest))


# vim: set sw=4 ts=4 expandtab:
