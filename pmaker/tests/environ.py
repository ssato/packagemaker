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
from pmaker.environ import *
from pmaker.globals import PKG_FORMATS, COMPRESSORS

import unittest


# TODO: What to check for?
class TestFunctions(unittest.TestCase):

    def test_hostname(self):
        self.assertNotEquals(hostname(), "")

    def test_get_arch(self):
        self.assertNotEquals(get_arch(), "")

    def test_get_distribution(self):
        (os, version, arch) = get_distribution()

    def test_get_package_format(self):
        pfmt = get_package_format()
        self.assertTrue(pfmt in PKG_FORMATS)

    def test_is_git_available(self):
        is_git_available()

    def test_get_username(self):
        self.assertNotEquals(get_username(), "")

    def test_get_email(self):
        self.assertNotEquals(get_email(), "")

    def test_get_fullname(self):
        self.assertNotEquals(get_fullname(), "")

    def test_get_compressor(self):
        (cmd, ext, am_opt) = get_compressor()

        cmds = [c for c, _e, _a in COMPRESSORS]
        exts = [e for _c, e, _a in COMPRESSORS]
        am_opts = [a for _c, _e, a in COMPRESSORS]

        self.assertTrue(cmd in cmds)
        self.assertTrue(ext in exts)
        self.assertTrue(am_opt in am_opts)


class TestEnv(unittest.TestCase):

    def test__init__(self):
        env = Env()
        self.assertTrue(isinstance(env, Bunch))

    def test__attrs(self):
        env = Env()

        if json is not None:
            self.assertFalse(env.json is None)

        if yaml is not None:
            self.assertFalse(env.yaml is None)


# vim:sw=4 ts=4 et:
