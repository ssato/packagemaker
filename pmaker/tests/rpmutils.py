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
from pmaker.rpmutils import *
from pmaker.utils import checksum
from pmaker.models.FileInfo import FileInfo, DirInfo

import random
import unittest


NULL_DICT = dict()


class TestFunctions(unittest.TestCase):

    def test_rpmh2nvrae__no_rpmdb(self):
        h = dict(name="foo", version="0.1", release="1", arch="i386", epoch="0")
        d = rpmh2nvrae(h)

        self.assertNotEquals(d, NULL_DICT)
        self.assertEquals(d["name"], "foo")

    def test_rpmh2nvrae(self):
        hs = [h for h in ts().dbMatch("name", "bash")]
        for h in hs:
            d = rpmh2nvrae(h)

            self.assertNotEquals(d, NULL_DICT)
            self.assertEquals(d["name"], "bash")

    def test_srcrpm_name_by_rpmspec(self):
        """FIXME: Implement tests for this function"""
        pass

    def test_srcrpm_name_by_rpmspec_2(self):
        """FIXME: Implement tests for this function"""
        pass

    def test_info_by_path(self):
        d = info_by_path("/bin/bash")
        self.assertNotEquals(d, NULL_DICT)

        for key in RPM_FI_KEYS:
            self.assertTrue(d.has_key(key))

    def test_filelist(self):
        """FIXME: Implement tests for this function"""
        #db = filelist()
        pass

    def test_rpm_search_provides_by_path(self):
        d = rpm_search_provides_by_path("/bin/bash")
        self.assertNotEquals(d, NULL_DICT)

    def test_rpm_attr(self):
        fi = FileInfo("/dummy/path", 33204, 0, 0, checksum(),NULL_DICT)
        self.assertEquals(rpm_attr(fi), "%attr(0664, -, -) ")

        fi = FileInfo("/bin/foo", 33261, 1, 1, checksum(),NULL_DICT)
        self.assertEquals(rpm_attr(fi), "%attr(0755, bin, bin) ")

        fi = DirInfo("/bin/bar/", 33204, 1, 1, checksum(),NULL_DICT)
        self.assertEquals(rpm_attr(fi), "%attr(0664, bin, bin) %dir ")


# vim: set sw=4 ts=4 expandtab:
