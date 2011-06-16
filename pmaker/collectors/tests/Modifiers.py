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
from pmaker.collectors.Modifiers import *
from pmaker.models.FileInfo import FileInfo
from pmaker.utils import checksum

import logging
import os.path
import unittest


NULL_DICT = dict()



class TestFileInfoModifier(unittest.TestCase):
    
    def setUp(self):
        self.modifier = FileInfoModifier()

    def test_update(self):
        fi = FileInfo("/dummy/path", 33204, 0, 0, checksum(), NULL_DICT)
        self.assertEquals(fi, self.modifier.update(fi))



class TestDestdirModifier(unittest.TestCase):

    def test_rewrite_with_destdir__normal(self):
        self.assertEquals(DestdirModifier("/a/b").rewrite_with_destdir("/a/b/c"), "/c")
        self.assertEquals(DestdirModifier("/a/b/").rewrite_with_destdir("/a/b/c"), "/c")

    def test_rewrite_with_destdir__no_destdir(self):
        try:
            DestdirModifier("/x/y/").rewrite_with_destdir("/a/b/c")
        except RuntimeError:
            pass

    def test_update(self):
        fileinfo = FileInfo("/a/b/c", 33204, 0, 0, checksum(), NULL_DICT)
        modifier = DestdirModifier("/a/b")

        new_fileinfo = modifier.update(fileinfo)
        self.assertEquals(new_fileinfo.target, "/c")



class TestOwnerModifier(unittest.TestCase):

    def test_wo_uid_and_gid(self):
        fileinfo = FileInfo("/a/b/c", 33204, 1, 1, checksum(), NULL_DICT)
        modifier = OwnerModifier()

        modifier.update(fileinfo)

        self.assertEquals(fileinfo.uid, 0)
        self.assertEquals(fileinfo.gid, 0)

    def test_w_uid_and_gid(self):
        fileinfo = FileInfo("/a/b/c", 33204, 1, 1, checksum(), NULL_DICT)
        modifier = OwnerModifier(100, 100)

        modifier.update(fileinfo)

        self.assertEquals(fileinfo.uid, 100)
        self.assertEquals(fileinfo.gid, 100)


# vim: set sw=4 ts=4 expandtab:
