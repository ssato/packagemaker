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
from pmaker.tests.common import setup_workdir, cleanup_workdir, selfdir

import pmaker.backend.autotools.single.tgz as T
import pmaker.backend.tests.common as TC

import logging
import os
import os.path
import unittest


class Test_00_Backend(unittest.TestCase):

    def setUp(self):
        logging.getLogger().setLevel(logging.WARN)  # suppress log messages

        self.workdir = setup_workdir()
        self.listfile = TC.dump_filelist(self.workdir)

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def mk_backend(self, step="build"):
        tmplpath = os.path.abspath(
            os.path.join(selfdir(), "../../", "templates")
        )
        #logging.warn("tmplpath = " + tmplpath)

        args = "-n foo -w %s --template-path %s -v" % (self.workdir, tmplpath)
        args += " --driver autotools.single.tgz --stepto %s %s" % \
            (step, self.listfile)

        return TC.init_pkgdata(args)

    def try_run(self, step):
        backend = T.Backend(self.mk_backend(step))
        TC.try_run(backend)

        self.assertTrue(os.path.exists(backend.marker_path({"name": step})))

        return backend

    def test_00_setup(self):
        self.try_run(STEP_SETUP)

    def test_01_preconfigure(self):
        self.try_run(STEP_PRECONFIGURE)

    def test_02_configure(self):
        self.try_run(STEP_CONFIGURE)

    def test_03_run__sbuild(self):
        backend = self.try_run(STEP_SBUILD)
        p = backend.pkgdata

        # e.g. /tmp/pmaker-testsOePcyh/foo-0.0.1/foo-0.0.1.tar.xz
        stgz = os.path.join(
            backend.workdir,
            "%s-%s.tar.%s" % (p.name, p.pversion, p.compressor.ext)
        )
        self.assertTrue(os.path.exists(stgz))

    def test_04_run__build(self):
        self.try_run(STEP_BUILD)  # same as sbuild in actual.


# vim:sw=4 ts=4 et:
