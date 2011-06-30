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
from pmaker.collectors.Filters import *
from pmaker.models.FileInfo import *

import unittest



class TestUnsupportedTypesFilter(unittest.TestCase):

    def setUp(self):
        self.filter = UnsupportedTypesFilter()

    def test__pred__supported(self):
        fi = FileInfo("/dummy/path", 33204, 0, 0, checksum(), dict())
        self.assertFalse(self.filter._pred(fi))

    def test__pred__unsupported(self):
        fi = UnknownInfo("/dummy/path")
        self.assertTrue(self.filter._pred(fi))


# vim: set sw=4 ts=4 expandtab:
