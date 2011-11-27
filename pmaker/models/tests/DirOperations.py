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
#
from pmaker.models.DirOperations import DirOperations
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.models.FileInfo import DirInfo
from pmaker.tests.common import setup_workdir, cleanup_workdir

import os
import os.path
import tempfile
import unittest


class TestDirOperations(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_remove(self):
        path = os.path.join(self.workdir, "test0")
        os.makedirs(path)

        DirOperations.remove(path)
        self.assertFalse(os.path.exists(path))

    def test_copy_main(self):
        path = os.path.join(self.workdir, "test0")
        os.makedirs(path)

        dest = os.path.join(self.workdir, "test1")
        fi = FileInfoFactory().create(path)

        DirOperations.copy_main(fi, dest)
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.isdir(dest))

    def test_create(self):
        path = dest = os.path.join(self.workdir, "test0")
        fi = DirInfo(path, create=True)

        DirOperations.create(fi, dest)
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.isdir(dest))


# vim:sw=4 ts=4 et:
