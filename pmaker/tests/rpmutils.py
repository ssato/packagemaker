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

import os
import random
import unittest


NULL_DICT = dict()


class TestFunctions(unittest.TestCase):

    def test_rpmh2nvrae__no_rpmdb(self):
        h = dict(
            name="foo",
            version="0.1",
            release="1",
            arch="i386",
            epoch="0",
        )
        d = rpmh2nvrae(h)

        self.assertNotEquals(d, NULL_DICT)
        self.assertEquals(d["name"], "foo")
        self.assertEquals(d["version"], "0.1")
        self.assertEquals(d["release"], "1")
        self.assertEquals(d["arch"], "i386")
        self.assertEquals(d["epoch"], "0")

    def test_rpmh2nvrae__no_rpmdb__epoch_is_None(self):
        h = dict(
            name="foo",
            version="0.1",
            release="1",
            arch="i386",
            epoch=None,
        )
        d = rpmh2nvrae(h)

        self.assertNotEquals(d, NULL_DICT)
        self.assertEquals(d["name"], "foo")
        self.assertEquals(d["version"], "0.1")
        self.assertEquals(d["release"], "1")
        self.assertEquals(d["arch"], "i386")
        self.assertEquals(d["epoch"], "0")

    def test_rpmh2nvrae__no_rpmdb__epoch_is_a_whitespace(self):
        h = dict(
            name="foo",
            version="0.1",
            release="1",
            arch="i386",
            epoch=" ",
        )
        d = rpmh2nvrae(h)

        self.assertNotEquals(d, NULL_DICT)
        self.assertEquals(d["name"], "foo")
        self.assertEquals(d["version"], "0.1")
        self.assertEquals(d["release"], "1")
        self.assertEquals(d["arch"], "i386")
        self.assertEquals(d["epoch"], "0")

    def test_rpmh2nvrae__w_rpmdb__no_epoch(self):
        hs = [h for h in ts().dbMatch("name", "bash")]
        for h in hs:
            d = rpmh2nvrae(h)

            self.assertNotEquals(d, NULL_DICT)
            self.assertEquals(d["name"], "bash")
            self.assertEquals(d["epoch"], "0")

    def test_rpmh2nvrae__w_rpmdb__w_epoch(self):
        hs = [h for h in ts().dbMatch("name", "bind-utils")]
        for h in hs:
            d = rpmh2nvrae(h)

            self.assertNotEquals(d, NULL_DICT)
            self.assertEquals(d["name"], "bind-utils")
            self.assertNotEquals(d["epoch"], "0")

    def test_srcrpm_name_by_rpmspec(self):
        """test_srcrpm_name_by_rpmspec: FIXME: Implement this"""
        pass

    def test_srcrpm_name_by_rpmspec_2(self):
        """test_srcrpm_name_by_rpmspec_2: FIXME: Implement this"""
        pass

    def test_info_by_path(self):
        d = info_by_path("/bin/bash")
        self.assertNotEquals(d, NULL_DICT)

        for key in RPM_FI_KEYS:
            self.assertTrue(key in d)

    def test_filelist(self):
        if not os.environ.get("RUN_TIME_CONSUMING_TESTS", False):
            logging.warn("set RUN_TIME_CONSUMING_TESTS=1 to run this test")
            return

        db = filelist()
        p = db.get("/bin/bash")

        self.assertNotEquals(p, NULL_DICT)
        self.assertEquals(p["name"], "bash")

    def test_rpm_search_provides_by_path(self):
        d = rpm_search_provides_by_path("/bin/bash")
        self.assertNotEquals(d, NULL_DICT)

    def test_rpm_attr(self):
        fi = FileInfo("/dummy/path", "0664")
        self.assertEquals(rpm_attr(fi), "%attr(0664, -, -) ")

        fi = FileInfo("/bin/foo", "0755", 1, 1)
        self.assertEquals(rpm_attr(fi), "%attr(0755, bin, bin) ")

        fi = DirInfo("/bin/bar/", "0664", 1, 1)
        self.assertEquals(rpm_attr(fi), "%attr(0664, bin, bin) %dir ")

        fi = FileInfo("/bin/baz", "0700", "root", "bin")
        self.assertEquals(rpm_attr(fi), "%attr(0700, -, bin) ")

        fi = DirInfo("/bin")
        self.assertEquals(rpm_attr(fi), "%dir ")


# vim:sw=4 ts=4 et:
