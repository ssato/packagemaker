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
from pmaker.makers.RpmPackageMaker import *
from pmaker.collectors.Collectors import FilelistCollector
from pmaker.globals import *
from pmaker.utils import rm_rf
from pmaker.config import Config
from pmaker.package import Package

import glob
import logging
import optparse
import os
import os.path
import random
import sys
import tempfile
import unittest



class Test_00_AutotoolsRpmPackageMaker(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        paths = [
            "#/etc/aliases.db",
            "/etc/auto.*",
            "/etc/hosts",
            "/etc/httpd/conf.d/*",
            "/etc/modprobe.d/*",
            "/etc/rc.d/init.d",
            "/etc/rc.d/rc",
            "/etc/reoslv.conf",
            "/etc/reslv.conf",  # should not be exist.
            "/etc/resolv.conf",
            "/etc/security/access.conf",
            "/etc/security/limits.conf",
            "/etc/skel",
            "/etc/system-release",
        ]
        paths = [p for p in paths if os.path.exists(p)]

        listfile = os.path.join(self.workdir, "files.list")
        open(listfile, "w").write("\n".join(paths))

        option_values = {
            "name": "foo",
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fis = fc.collect()

        defaults = Config.defaults()
        defaults["workdir"] = self.workdir
        defaults["name"] = "foo"
        defaults["no_mock"] = True

        options = optparse.Values(defaults)
        package = Package(options)

        self.pmaker = AutotoolsRpmPackageMaker(package, fis, options)
        self.pmaker.template_paths = [os.path.join(os.getcwd(), "templates")]

        logging.getLogger().setLevel(logging.WARNING) # suppress log messages

    def tearDown(self):
        rm_rf(self.workdir)

    def helper_run_upto_step(self, step):
        self.pmaker.upto = step

        try:
            self.pmaker.run()
        except SystemExit:
            pass

        self.assertTrue(os.path.exists(self.pmaker.touch_file(step)))

    def test_01_preconfigure(self):
        self.helper_run_upto_step(STEP_PRECONFIGURE)

    def test_02_configure(self):
        self.helper_run_upto_step(STEP_CONFIGURE)

    def test_03_run__sbuild(self):
        self.helper_run_upto_step(STEP_SBUILD)

    def test_04_run__build(self):
        self.helper_run_upto_step(STEP_BUILD)


# vim: set sw=4 ts=4 expandtab:
