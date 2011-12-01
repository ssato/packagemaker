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
from pmaker.parser import *
from pmaker.models.Bunch import Bunch
from pmaker.models.FileObjects import XObject
from pmaker.tests.common import setup_workdir, cleanup_workdir

import os
import os.path
import sys
import tempfile
import unittest


class Test_parser(unittest.TestCase):

    def test_00_parse_single(self):
        self.assertEquals(parse_single(""), "")
        self.assertEquals(parse_single("0"), 0)
        self.assertEquals(parse_single("123"), 123)
        self.assertEquals(parse_single("True"), True)
        self.assertEquals(parse_single("a string"), "a string")
        self.assertEquals(parse_single("0.1"), "0.1")
        self.assertEquals(
            parse_single("    a string contains extra whitespaces     "),
            "a string contains extra whitespaces"
        )

    def test_01_parse_list(self):
        self.assertEquals(parse_list(""), [])
        self.assertEquals(parse_list("a,b"), ["a", "b"])
        self.assertEquals(parse_list("1,2"), [1, 2])
        self.assertEquals(parse_list("a,b,"), ["a", "b"])
        self.assertEquals(parse_list("a|b|", "|"), ["a", "b"])

    def test_02_parse_attrlist(self):
        self.assertEquals(
            parse_attrlist("requires:bash,zsh"),
            [('requires', ['bash', 'zsh'])]
        )
        self.assertEquals(
            parse_attrlist("obsoletes:sysdata;conflicts:sysdata-old"),
            [('obsoletes', ['sysdata']), ('conflicts', ['sysdata-old'])]
        )

    def test_03_parse(self):
        pass

    def test_04_parse_line_of_filelist(self):
        line = "/etc/resolv.conf"
        (paths, attrs) = parse_line_of_filelist(line + " \n")

        self.assertEquals(paths[0], line)
        self.assertEquals(attrs, {})

        line2 = line + ",install_path=/var/lib/network/resolv.conf,uid=0,gid=0"
        (paths, attrs) = parse_line_of_filelist(line2 + " \n")

        self.assertEquals(paths[0], line)
        self.assertEquals(
            attrs.install_path, "/var/lib/network/resolv.conf"
        )
        self.assertEquals(attrs.uid , 0)
        self.assertEquals(attrs.gid , 0)


# vim:sw=4 ts=4 et:
