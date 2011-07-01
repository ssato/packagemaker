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
from pmaker.cui import main as cui_main
from pmaker.utils import rm_rf

import glob
import logging
import os
import os.path
import random
import sys
import tempfile
import unittest



class Test_cui_main__multi_files_tgz(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.pmworkdir = os.path.join(self.workdir, "pm")
        self.listfile = os.path.join(self.workdir, "files.list")
        self.template_path = os.path.join(os.getcwd(), "templates")

        logging.getLogger().setLevel(logging.DEBUG)

    def tearDown(self):
        rm_rf(self.workdir)

    def helper_run_with_args(self, args):
        try:
            cui_main(args.split())
        except SystemExit:
            pass

        #self.assertTrue(...something_to_confirm_access...)

    def test_00_generated_files(self):
        targets = [os.path.join(self.workdir, p) for p in ("aaa.txt", "bbb.txt", "c/d/e/f.txt")]

        os.makedirs(os.path.dirname(targets[-1]))
        for t in targets:
            os.system("touch " + t)

        open(self.listfile, "w").write("\n".join(targets))

        args = "argv0 --name foobar --template-path %s -w %s --format %s %s" % \
            (self.template_path, self.pmworkdir, "tgz", self.listfile)
        self.helper_run_with_args(args)

    def test_01_system_files(self):
        paths = [
            "/etc/aliases.db",
            "/etc/at.deny",
            "/etc/auto.master",
            "/etc/hosts",
            "/etc/httpd/conf/httpd.conf",
            "/etc/modprobe.d/blacklist.conf",
            "/etc/rc.d/init.d",
            "/etc/rc.d/rc",
            "/etc/resolv.conf",
            "/etc/secure.tty",
            "/etc/security/access.conf",
            "/etc/security/limits.conf",
            "/etc/shadow",
            "/etc/skel",
            "/etc/system-release",
            "/etc/sudoers",
        ]
        targets = [p for p in paths if os.path.exists(p)]

        open(self.listfile, "w").write("\n".join(targets))

        args = "argv0 --name foobar --template-path %s -w %s -vv --format %s %s" % \
            (self.template_path, self.pmworkdir, "tgz", self.listfile)
        self.helper_run_with_args(args)


# vim: set sw=4 ts=4 expandtab:
