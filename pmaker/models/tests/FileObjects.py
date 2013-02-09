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
from pmaker.utils import checksum
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.models.FileObjects as FO

import os
import random
import tempfile
import unittest


NULL_DICT = dict()


class TestFileObject(unittest.TestCase):

    def setUp(self):
        self.path = None

        for p in ("/etc/hosts", "/etc/resolv.conf", "/etc/bashrc"):
            if os.path.exists(p):
                self.path = p
                break

        assert self.path is not None, \
            "No any paths for testing exist! Aborting..."

    def test__init__w_path(self):
        fo = FO.FileObject(self.path)

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.path, self.path)

    def test__init__w_path_and_mode(self):
        for mode in ("0644", "0755", "1600"):
            fo = FO.FileObject(self.path, mode)

            self.assertTrue(isinstance(fo, FO.FileObject))
            self.assertEquals(fo.mode, mode)

    def test__init__w_path_and_src(self):
        src = "/path/to/src"
        fo = FO.FileObject(self.path, src=src)

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.src, src)


class TestDirObject(unittest.TestCase):

    def setUp(self):
        self.path = None

        for p in ("/etc/hosts", "/etc/resolv.conf", "/etc/bashrc"):
            if os.path.exists(p):
                self.path = p
                break

        assert self.path is not None, \
            "No any paths for testing exist! Aborting..."

    def test__init__w_path(self):
        fo = FO.DirObject(self.path)

        self.assertTrue(isinstance(fo, FO.DirObject))
        self.assertEquals(fo.path, self.path)


class TestSymlinkInfo(unittest.TestCase):

    def setUp(self):
        self.linkto = None

        for p in ("/etc/hosts", "/etc/resolv.conf", "/etc/bashrc"):
            if os.path.exists(p):
                self.linkto = p
                break

        assert self.linkto is not None, \
            "No any paths for testing exist! Aborting..."

        self.workdir = setup_workdir()

        self.path = os.path.join(self.workdir, "test.symlink")
        os.symlink(self.linkto, self.path)

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test__init__w_path(self):
        fo = FO.SymlinkObject(self.path, self.linkto)

        self.assertTrue(isinstance(fo, FO.SymlinkObject))
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.linkto, self.linkto)

    def test__init__w_path_and_linkto(self):
        dummy_linkto = "/path/to/linkto"
        fo = FO.SymlinkObject(self.path, linkto=dummy_linkto)

        self.assertTrue(isinstance(fo, FO.SymlinkObject))
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.linkto, dummy_linkto)


# vim:sw=4:ts=4:et:
