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
from pmaker.tests.common import setup_workdir, cleanup_workdir, \
    selfdir, TOPDIR

import pmaker.app as A

import os
import os.path
import sys
import unittest


class Test_00_main(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def helper(self, config, extra_args=[]):
        curdir = selfdir()
        conf = os.path.join(curdir, config)
        tmpldir = os.path.join(TOPDIR, "templates")
        logfile = os.path.join(self.workdir, "run.log")

        args = [
            "dummy_argv0",
            "-n", "foo",
            "-w", self.workdir,
            "-C", conf,
            "-P", tmpldir,
            "-L", logfile,
        ] + extra_args

        rc = A.main(args)

        self.assertEquals(rc, 0)

    def test_00_run_w_ini_conf_and_filelist(self):
        filelist = os.path.join(selfdir(), "config_example_00_filelist")

        self.helper("config_example_01.ini", [filelist])

    def test_01_run_w_json_conf(self):
        self.helper("config_example_01.json")

    def test_02_run_w_yaml_conf(self):
        self.helper("config_example_01.yaml")


# vim:sw=4:ts=4:et:
