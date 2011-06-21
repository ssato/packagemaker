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

import unittest


# TODO: What to check for?
class TestFunctions(unittest.TestCase):

    def test_hostname(self):
        self.assertNotEquals(hostname(), "")

    def test_get_arch(self):
        self.assertNotEquals(get_arch(), "")

    def test_get_distribution(self):
        (os, version) = get_distribution()

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


# vim: set sw=4 ts=4 expandtab:
