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
from pmaker.models.FileOperations import *
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.models.FileInfo import FileInfo
from pmaker.utils import checksum, rm_rf

import copy
import os
import os.path
import stat
import tempfile
import unittest



try:
    import xattr
    PYXATTR_ENABLED = True
except ImportError:
    PYXATTR_ENABLED = False



class TestFileOperations(unittest.TestCase):

    def test_equals(self):
        lhs = FileInfoFactory().create("/etc/resolv.conf")
        rhs = copy.copy(lhs)
        setattr(rhs, "other_attr", "xyz")
        
        self.assertTrue(FileOperations.equals(lhs, rhs))
        
        rhs.mode = "755"
        self.assertFalse(FileOperations.equals(lhs, rhs))

    def test_equivalent(self):
        class FakeFileInfo(object):
            checksum = checksum()

        lhs = FakeFileInfo(); rhs = FakeFileInfo()
        self.assertTrue(FileOperations.equivalent(lhs, rhs))

        rhs.checksum = checksum("/etc/resolv.conf")
        self.assertFalse(FileOperations.equivalent(lhs, rhs))

    def test_permission(self):
        file0 = "/etc/resolv.conf"
        if os.path.exists(file0):
            mode = os.lstat(file0).st_mode
            expected = oct(stat.S_IMODE(mode & 0777))
            self.assertEquals(expected, FileOperations.permission(mode))

        gshadow = "/etc/gshadow-"
        if os.path.exists(gshadow):
            mode = os.lstat(gshadow).st_mode
            self.assertEquals("0000", FileOperations.permission(mode))



class TestFileOperations__with_writes(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.testfile1 = os.path.join(self.workdir, "test1.txt")
        os.system("touch " + self.testfile1)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_copy_main__and__remove(self):
        fileinfo = FileInfoFactory().create(self.testfile1)
        dest = self.testfile1 + ".2"

        FileOperations.copy_main(fileinfo, dest, use_pyxattr=False)
        self.assertTrue(os.path.exists(dest))

        FileOperations.remove(dest)
        self.assertFalse(os.path.exists(dest))

    def test_copy_main__and__remove__with_pyxattr(self):
        if not PYXATTR_ENABLED:
            logging.warn("Could not load pyxattr module. Skip this test")
            return

        fileinfo = FileInfoFactory().create(self.testfile1)
        dest = self.testfile1 + ".2"

        FileOperations.copy_main(fileinfo, dest, use_pyxattr=True)
        self.assertTrue(os.path.exists(dest))

        FileOperations.remove(dest)
        self.assertFalse(os.path.exists(dest))

    def test_copy__src_and_dst_are_same(self):
        fileinfo = FileInfoFactory().create(self.testfile1)

        self.assertRaises(AssertionError, FileOperations.copy, fileinfo, fileinfo.path)

    def test_copy__not_copyable(self):
        class NotCopyableFileInfo(FileInfo):
            is_copyable = False

            def __init__(self, path):
                mode = os.lstat(path).st_mode
                uid = gid = 0
                csum = checksum(path)
                xattrs = dict()

                super(NotCopyableFileInfo, self).__init__(path, mode, uid, gid, csum, xattrs)

        fileinfo = NotCopyableFileInfo(self.testfile1)
        dest = self.testfile1 + ".2"

        self.assertFalse(FileOperations.copy(fileinfo, dest))

    def test_copy__exists(self):
        fileinfo = FileInfoFactory().create(self.testfile1)
        dest = self.testfile1 + ".2"

        FileOperations.copy(fileinfo, dest)

        self.assertFalse(FileOperations.copy(fileinfo, dest))

    def test_copy__exists__force(self):
        fileinfo = FileInfoFactory().create(self.testfile1)
        dest = self.testfile1 + ".2"

        self.assertTrue(FileOperations.copy(fileinfo, dest, force=True))

    def test_copy__mkdir(self):
        fileinfo = FileInfoFactory().create(self.testfile1)
        dest = os.path.join(self.workdir, "t", "test2.txt")

        self.assertTrue(FileOperations.copy(fileinfo, dest))


# vim: set sw=4 ts=4 expandtab:
