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
from pmaker.shell import *

import os.path
import unittest


class Test_shell(unittest.TestCase):

    def test_shell_success(self):
        if os.path.exists("/dev") and os.path.exists("/dev/null"):
            self.assertEquals(shell("echo ok > /dev/null"), 0)
            self.assertEquals(shell("ls null", "/dev"), 0)
            self.assertEquals(shell("ls null", "/dev", dryrun=True), 0)

    def test_shell_fail_as_expected(self):
        try:
            rc = shell("ls", "/root")
        except RuntimeError:
            pass


class Test_ThreadedCommand(unittest.TestCase):

    def test_run__00(self):
        cmd = "true"

        self.assertEquals(ThreadedCommand(cmd).run(), 0)

    def test_run__01_workdir(self):
        cmd = "true"
        workdir = "/tmp"

        self.assertEquals(ThreadedCommand(cmd, workdir).run(), 0)

    def test_run__02_stop_on_error(self):
        cmd = "false"
        tcmd = ThreadedCommand(cmd, stop_on_error=True)

        self.assertRaises(RuntimeError, tcmd.run)

    def test_run__03_timeout(self):
        cmd = "sleep 10"
        tcmd = ThreadedCommand(cmd, timeout=1)

        self.assertRaises(RuntimeError, tcmd.run)


# vim:sw=4:ts=4:et:
