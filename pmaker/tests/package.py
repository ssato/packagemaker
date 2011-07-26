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
from pmaker.package import *
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.config import Config

import glob
import optparse
import os
import os.path
import random
import unittest



class TestPackage(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.options = optparse.Values(Config.defaults())
        self.package = Package(self.options)

    def test__init_(self):
        self.assertTrue(isinstance(self.package, Package))

    def test_update(self):
        self.package.update(dict(foobar="baz"))

        self.assertTrue(self.package.foobar, "baz")

    def test_add_fileinfos(self):
        files = (p for p in random.sample(glob.glob("/etc/*"), 10) if os.access(p, os.R_OK))
        fis = [FileInfoFactory().create(p) for p in files]

        self.package.add_fileinfos(fis)

        self.assertNotEquals(self.package.fileinfos, [])
        self.assertEquals(self.package.fileinfos, fis)


# vim: set sw=4 ts=4 expandtab:
