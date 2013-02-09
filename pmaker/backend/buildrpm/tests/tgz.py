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
from pmaker.globals import STEP_SETUP, STEP_PRECONFIGURE, STEP_CONFIGURE, \
    STEP_SBUILD, STEP_BUILD
from pmaker.tests.common import cleanup_workdir

import pmaker.backend.tests.common as C

import os.path
import unittest


class Test_00_Backend(unittest.TestCase):

    def setUp(self):
        (self.workdir, self.listfile) = C.setup_workdir_and_listfile()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def get_backend_tester(self, step=STEP_SETUP):
        return C.BackendTester(
            self.workdir, self.listfile, step, "buildrpm.tgz"
        )

    def __assertExists(self, path):
        self.assertTrue(os.path.exists(path))

    def test_00_setup(self):
        bt = self.get_backend_tester(STEP_SETUP)
        self.assertTrue(bt.try_run())

        dumped_conf = os.path.join(bt.backend.workdir, "pmaker-config.json")
        self.__assertExists(dumped_conf)

    def test_01_preconfigure(self):
        bt = self.get_backend_tester(STEP_PRECONFIGURE)
        self.assertTrue(bt.try_run())

    def test_02_configure(self):
        bt = self.get_backend_tester(STEP_CONFIGURE)
        self.assertTrue(bt.try_run())

    def test_03_sbuild(self):
        bt = self.get_backend_tester(STEP_SBUILD)
        self.assertTrue(bt.try_run())

        p = bt.backend.pkgdata

        # e.g. /tmp/pmaker-testsOePcyh/foo-0.0.1/foo-0.0.1.tar.xz
        tgz = os.path.join(
            bt.backend.workdir,
            "%s-%s.tar.%s" % (p.name, p.pversion, p.compressor.ext)
        )
        self.__assertExists(tgz)

    def test_04_build(self):
        bt = self.get_backend_tester(STEP_BUILD)  # same as sbuild in actual.
        self.assertTrue(bt.try_run())

        p = bt.backend.pkgdata

        tgz = os.path.join(
            bt.backend.workdir,
            "%s-%s.tar.%s" % (p.name, p.pversion, p.compressor.ext)
        )
        self.__assertExists(tgz)


# vim:sw=4:ts=4:et:
