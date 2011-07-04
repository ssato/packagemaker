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
from pmaker.environ import get_arch
from tests.utils import *

import glob
import logging
import os
import os.path
import random
import unittest



class Test_00_single_file_rpm(unittest.TestCase):

    def setUp(self):
        self.workdir = helper_create_tmpdir()
        self.listfile = os.path.join(self.workdir, "files.list")
        self.template_path = os.path.join(os.getcwd(), "templates")

        p = PKG_0
        p["tpath"] = self.template_path
        p["wdir"] = self.workdir
        p["fmt"] = "rpm"

        args = "--name %(name)s --template-path %(tpath)s -w %(wdir)s --format %(fmt)s " % p
        self.args = args + self.listfile

        pnv = "%(name)s-%(version)s" % p

        rpm_pattern = os.path.join(self.workdir, pnv, pnv + "*")
        self.rpm_pattern = rpm_pattern

        logging.getLogger().setLevel(logging.WARN) # suppress log messages

    def tearDown(self):
        rm_rf(self.workdir)

    def test_00_generated_file__srpm(self):
        if not helper_is_rpm_based_system():
            return

        target = os.path.join(self.workdir, "aaa.txt")
        os.system("touch " + target)

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args + " --upto sbuild")

        rpms = glob.glob(self.rpm_pattern + "src.rpm")
        self.assertTrue(len(rpms) > 0)

    def test_01_generated_file__wo_mock(self):
        if not helper_is_rpm_based_system():
            return

        target = os.path.join(self.workdir, "aaa.txt")
        os.system("touch " + target)

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args + " --upto build --no-mock")

        rpms = glob.glob(self.rpm_pattern + "noarch.rpm")
        self.assertTrue(len(rpms) > 0)

    def test_02_generated_file__w_mock(self):
        if not helper_is_rpm_based_system():
            return

        target = os.path.join(self.workdir, "aaa.txt")
        os.system("touch " + target)

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args + " --upto build")

        rpms = glob.glob(self.rpm_pattern + "noarch.rpm")
        self.assertTrue(len(rpms) > 0)

    def test_03_system_file__no_conflicts__wo_mock(self):
        if not helper_is_rpm_based_system():
            return

        # These should be owned by no any other rpms:
        targets = [
            "/etc/aliases.db",
            "/etc/grub.conf",
            "/etc/mdadm.conf",
            "/etc/prelink.cache",
            "/etc/resolv.conf"
        ]

        target = random.choice([f for f in targets if os.path.exists(f) and os.access(f, os.R_OK)])

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args + " --upto build")

        rpms = glob.glob(self.rpm_pattern + "noarch.rpm")
        self.assertTrue(len(rpms) > 0)

    def test_04_system_file__conflicts__wo_mock(self):
        if not helper_is_rpm_based_system():
            return

        # These are owned by other rpms:
        targets = [
            "/etc/hosts",
            "/etc/sysctl.conf",
            "/etc/inittab",
            "/etc/bashrc",
            "/etc/sysconfig/network",
            "/etc/rc.d/rc.local",
        ]

        target = random.choice([f for f in targets if os.path.exists(f) and os.access(f, os.R_OK)])

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args + " --upto build")

        rpms = glob.glob(self.rpm_pattern + "noarch.rpm")
        self.assertTrue(len(rpms) > 0)

    def test_05_generated_file__wo_mock__w_arch(self):
        if not helper_is_rpm_based_system():
            return

        target = os.path.join(self.workdir, "aaa.txt")
        os.system("touch " + target)

        open(self.listfile, "w").write("%s\n" % target)

        helper_run_with_args(self.args + " --upto build --no-mock --arch")

        rpms = glob.glob(self.rpm_pattern + ".%s.rpm" % get_arch())
        self.assertTrue(len(rpms) > 0)


# vim: set sw=4 ts=4 expandtab:
