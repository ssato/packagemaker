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
from pmaker.options import *
from pmaker.models.Bunch import Bunch
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.parser as P

import optparse
import os
import os.path
import tempfile
import unittest


class Test_00_functions(unittest.TestCase):

    def test_01_setup_relations_option(self):
        p = optparse.OptionParser()
        p.add_option("", "--relations", **setup_relations_option())

        options, args = p.parse_args([])
        self.assertEquals(options.relations, "")

        relations_s = "obsoletes:mydata;conflicts:mydata-old"
        options, args = p.parse_args(
            ["--relations", relations_s]
        )
        expected = P.parse(relations_s)
        self.assertEquals(options.relations, expected)

    def test_02_set_workdir__absolute_workdir(self):
        workdir, name, version = ("/tmp/w", "foo", "0.0.1")
        self.assertEquals(
            "/tmp/w/foo-0.0.1",
            set_workdir(workdir, name, version)
        )

    def test_03_set_workdir__relative_workdir(self):
        workdir, name, version = ("../w", "foo", "0.0.1")
        abs_workdir = os.path.abspath(workdir)
        self.assertEquals(
            abs_workdir + "/foo-0.0.1",
            set_workdir(workdir, name, version)
        )


class Test_01_Options(unittest.TestCase):

    def test_00__init__wo_args(self):
        o = Options()
        o2 = Options()

        # pmaker.options.Options is not resolvable because it would be hide
        # (decorated) with pmaker.utils.singleton(). Here we use Bunch (parent
        # class of Options class) instead.
        self.assertTrue(isinstance(o, Bunch))
        self.assertEquals(o, o2)


# vim:sw=4 ts=4 et:
