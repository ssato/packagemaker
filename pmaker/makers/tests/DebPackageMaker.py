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
from pmaker.makers.DebPackageMaker import *
from pmaker.collectors.Collectors import FilelistCollector
from pmaker.globals import *
from pmaker.utils import memoize
from pmaker.config import Config
from pmaker.package import Package
from pmaker.tests.common import setup_workdir, cleanup_workdir

import logging
import optparse
import os
import os.path
import sys
import unittest



@memoize
def is_cmd_available(cmd="dpkg-buildpackage"):
    return os.system("which %s > /dev/null 2> /dev/null" % cmd) == 0



class Test_00_AutotoolsDebPackageMaker(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

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
            "format": "deb",
            "destdir": "",
            "ignore_owner": False,
        }

        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fis = fc.collect()

        defaults = Config.defaults()
        defaults["workdir"] = self.workdir
        defaults["name"] = "foo"

        options = optparse.Values(defaults)
        package = Package(options)

        self.pmaker = AutotoolsDebPackageMaker(package, fis, options)
        self.pmaker.template_paths = [os.path.join(os.getcwd(), "templates")]

        logging.getLogger().setLevel(logging.WARNING) # suppress log messages

    def tearDown(self):
        cleanup_workdir(self.workdir)

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
        if is_cmd_available("dpkg-buildpackage"):
            self.helper_run_upto_step(STEP_CONFIGURE)
        else:
            print >> sys.stderr, "dpkg-buildpackage is not available. Skip this test"

    def test_03_run__sbuild(self):
        if is_cmd_available("debuild"):
            self.helper_run_upto_step(STEP_SBUILD)
        else:
            print >> sys.stderr, "debuild is not available. Skip this test"

    def test_04_run__build(self):
        if is_cmd_available("debuild"):
            self.helper_run_upto_step(STEP_BUILD)
        else:
            print >> sys.stderr, "debuild is not available. Skip this test"


# vim: set sw=4 ts=4 expandtab:
