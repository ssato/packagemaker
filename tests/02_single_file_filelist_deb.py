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

import logging
import os
import os.path
import random
import sys
import tempfile
import unittest



class Test_cui_main__single_file_deb(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.pmworkdir = os.path.join(self.workdir, "pm")
        self.listfile = os.path.join(self.workdir, "files.list")
        self.template_path = os.path.join(os.getcwd(), "templates")

        logging.getLogger().setLevel(logging.WARNING) # suppress log messages

    def tearDown(self):
        rm_rf(self.workdir)

    def helper_run_with_args(self, args):
        try:
            cui_main(args.split())
        except SystemExit:
            pass

        #self.assertTrue(...something_to_confirm_access...)

    def test_00_generated_file__deb(self):
        if not os.path.exists("/etc/debian_version"):
            print >> sys.stderr, "This system does not look a Deb-based system."
            return

        target = os.path.join(self.workdir, "aaa.txt")
        os.system("touch " + target)

        open(self.listfile, "w").write("%s\n" % target)

        args = "pmaker_dummy --name foobar --template-paths %s -w %s -q --format %s %s" % \
            (self.template_path, self.pmworkdir, "deb", self.listfile)
        self.helper_run_with_args(args)


# vim: set sw=4 ts=4 expandtab:
