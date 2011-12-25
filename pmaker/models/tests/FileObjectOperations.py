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
from pmaker.models.FileObjectOperations import *
from pmaker.models.FileObjects import *
from pmaker.utils import checksum
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.models.FileObjectFactory as Factory

import copy
import os
import os.path
import stat
import tempfile
import unittest


class Test_00_functions(unittest.TestCase):

    def test_same_and_equals(self):
        lhs = FileObject("/etc/resolv.conf", mode="0644")
        rhs = copy.copy(lhs)
        setattr(rhs, "other_attr", "xyz")

        self.assertTrue(equals(lhs, rhs))
        self.assertTrue(same(lhs, rhs))

        rhs.path = "/xyz"
        self.assertFalse(equals(lhs, rhs))

        rhs.mode = "0755"
        self.assertFalse(same(lhs, rhs))


class Test_01_FileOps__with_side_effects(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        self.testfile1 = os.path.join(self.workdir, "test1.txt")
        open(self.testfile1, "w").write("test1\n")

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_copy_impl_and_remove(self):
        fo = Factory.create(self.testfile1)
        dest = self.testfile1 + ".2"

        FileOps.copy_impl(fo, dest)
        self.assertTrue(os.path.exists(dest))

        FileOps.remove(dest)
        self.assertFalse(os.path.exists(dest))

    def test_copy__src_and_dst_are_same(self):
        fo = Factory.create(self.testfile1)
        self.assertRaises(AssertionError, FileOps.copy, fo, fo.path)

    def test_copy__not_copyable(self):
        class NotCopyableFileObject(FileObject):
            is_copyable = False

        fo = NotCopyableFileObject(self.testfile1)
        dest = self.testfile1 + ".2"

        self.assertFalse(FileOps.copy(fo, dest))

    def test_copy__exists(self):
        fo = Factory.create(self.testfile1)
        dest = self.testfile1 + ".2"

        FileOps.copy(fo, dest)

        self.assertFalse(FileOps.copy(fo, dest))

    def test_copy__exists__force(self):
        fo = Factory.create(self.testfile1)
        dest = self.testfile1 + ".2"

        self.assertTrue(FileOps.copy(fo, dest, force=True))

    def test_copy__mkdir(self):
        fo = Factory.create(self.testfile1)
        dest = os.path.join(self.workdir, "t", "test2.txt")

        self.assertTrue(FileOps.copy(fo, dest))

    def test_copy__create(self):
        path = dest = self.testfile1 + ".3"

        fo = FileObject(path, create=1, content="xyz\n")
        dest = os.path.join(self.workdir, "t", "test3.txt")

        self.assertTrue(FileOps.copy(fo, dest))


# vim:sw=4 ts=4 et:
