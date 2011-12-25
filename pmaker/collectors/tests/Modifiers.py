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
from pmaker.models.FileObjects import FileObject

import logging
import os.path
import unittest


class Test_00_FileObjectModifier(unittest.TestCase):

    def setUp(self):
        self.modifier = FileObjectModifier()

    def test_update(self):
        fo = FileObject("/dummy/path")
        self.assertEquals(fo, self.modifier.update(fo))


class Test_01_DestdirModifier(unittest.TestCase):

    def test_rewrite_with_destdir__normal(self):
        self.assertEquals(
            DestdirModifier("/a/b").rewrite_with_destdir("/a/b/c"),
            "/c"
        )
        self.assertEquals(
            DestdirModifier("/a/b/").rewrite_with_destdir("/a/b/c"),
            "/c"
        )

    def test_00_rewrite_with_destdir__no_destdir(self):
        try:
            DestdirModifier("/x/y/").rewrite_with_destdir("/a/b/c")
        except RuntimeError:
            pass

    def test_01_update(self):
        fo = FileObject("/a/b/c")
        modifier = DestdirModifier("/a/b")

        new_fo = modifier.update(fo)
        self.assertEquals(new_fo.install_path, "/c")


class Test_02_OwnerModifier(unittest.TestCase):

    def test_00_wo_uid_and_gid(self):
        fo = FileObject("/a/b/c", uid=1, gid=1)
        modifier = OwnerModifier()  # owner_{uid,gid} = 0

        fo = modifier.update(fo)

        self.assertEquals(fo.uid, 0)
        self.assertEquals(fo.gid, 0)

    def test_01_w_uid_and_gid(self):
        fo = FileObject("/a/b/c", uid=1, gid=1)
        modifier = OwnerModifier(100, 100)

        fo = modifier.update(fo)

        self.assertEquals(fo.uid, 100)
        self.assertEquals(fo.gid, 100)


class Test_03_AttributeModifier(unittest.TestCase):

    def test_00_update(self):
        fo = FileObject("/a/b/c", mode="0644", uid=1, gid=1)
        modifier = AttributeModifier()

        fo = modifier.update(fo, dict(mode="0755", uid=0))

        self.assertEquals(fo.mode, "0755")
        self.assertEquals(fo.uid, 0)


# vim:sw=4 ts=4 et:
