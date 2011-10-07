#
# Copyright (C) 2011 Satoru SATOH <ssato @ redhat.com>
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
from pmaker.utils import checksum
from pmaker.tests.common import setup_workdir, cleanup_workdir

import copy
import os
import os.path
import stat
import tempfile
import unittest


class Test_00_FileOperations(unittest.TestCase):

    def test_equals(self):
        lhs = FileInfo("/etc/resolv.conf", mode="0644")
        rhs = copy.copy(lhs)
        setattr(rhs, "other_attr", "xyz")
        
        self.assertTrue(FileOperations.equals(lhs, rhs))
        
        rhs.mode = "0755"
        self.assertFalse(FileOperations.equals(lhs, rhs))



class Test_01_FileOperations__with_side_effects(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        self.testfile1 = os.path.join(self.workdir, "test1.txt")
        open(self.testfile1, "w").write("test1\n")

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_copy_main__and__remove(self):
        fileinfo = FileInfoFactory().create(self.testfile1)
        dest = self.testfile1 + ".2"

        FileOperations.copy_main(fileinfo, dest)
        self.assertTrue(os.path.exists(dest))

        FileOperations.remove(dest)
        self.assertFalse(os.path.exists(dest))

    def test_copy__src_and_dst_are_same(self):
        fileinfo = FileInfoFactory().create(self.testfile1)

        self.assertRaises(AssertionError, FileOperations.copy, fileinfo, fileinfo.path)

    def test_copy__not_copyable(self):
        class NotCopyableFileInfo(FileInfo):
            is_copyable = False

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

    def test_copy__create(self):
        path = dest = self.testfile1 + ".3"

        fileinfo = FileInfo(path, create=1, content="xyz\n")
        dest = os.path.join(self.workdir, "t", "test3.txt")

        self.assertTrue(FileOperations.copy(fileinfo, dest))


# vim: set sw=4 ts=4 expandtab:
