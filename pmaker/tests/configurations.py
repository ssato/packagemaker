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
from pmaker.configurations import Config, _defaults
from pmaker.models.Bunch import Bunch
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.environ as E

import os
import os.path
import unittest


class Test_01_functions(unittest.TestCase):

    def test_00__defaults(self):
        dfs = _defaults(E.Env())

        self.assertTrue(isinstance(dfs, Bunch))


class Test_02_Config(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        self.config = os.path.join(self.workdir, "test.config")

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_00__init__w_norc(self):
        cfg = Config(norc=True)
        dfs = _defaults(E.Env())  # reference of cfg.

        for k, v in dfs.iteritems():
            self.assertEquals(getattr(cfg, k), v)

    def test_01__norc_and_load_config(self):
        cfg = Config(norc=True)
        dfs = _defaults(E.Env())

        # TBD: It looks pmaker.anycfg must be changed: typical one is defauls
        # configuraion should be overloaded by profile's configurations in
        # IniConfigParser.


# vim:sw=4 ts=4 et:
