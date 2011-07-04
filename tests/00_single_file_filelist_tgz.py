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
from pmaker.utils import rm_rf
from tests.utils import *

import glob
import logging
import os
import os.path
import unittest



class Test_00_single_file_tgz(unittest.TestCase):

    def setUp(self):
        self.workdir = helper_create_tmpdir()
        self.pmworkdir = os.path.join(self.workdir, "pm")
        self.listfile = os.path.join(self.workdir, "files.list")
        self.template_path = os.path.join(os.getcwd(), "templates")

        p = PKG_0
        p["tpath"] = self.template_path
        p["wdir"] = self.pmworkdir
        p["fmt"] = "tgz"

        args = "--name %(name)s --template-path %(tpath)s -w %(wdir)s --format %(fmt)s " % p
        self.args = args + self.listfile

        pnv = "%(name)s-%(version)s" % p

        tgz = os.path.join(self.pmworkdir, pnv, pnv + ".tar." + helper_get_compressor_ext())
        self.tgz = tgz

        logging.getLogger().setLevel(logging.WARNING) # suppress log messages

    def tearDown(self):
        rm_rf(self.workdir)

    def test_00_generated_file(self):
        target = os.path.join(self.workdir, "aaa.txt")
        os.system("touch " + target)

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args)

        self.assertTrue(os.path.exists(self.tgz))

    def test_01_system_file(self):
        target = helper_random_system_files(1)

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args)

        self.assertTrue(os.path.exists(self.tgz))


# vim: set sw=4 ts=4 expandtab:
