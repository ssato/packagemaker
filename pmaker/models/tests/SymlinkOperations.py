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
from pmaker.models.SymlinkOperations import SymlinkOperations
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.models.FileInfo import SymlinkInfo
from pmaker.tests.common import setup_workdir, cleanup_workdir

import os
import os.path
import unittest


class TestSymlinkOperations(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        src = os.path.join(self.workdir, "test.txt")
        open(src, "w").write("test\n")

        self.path = os.path.join(self.workdir, "symlink.txt")
        os.symlink(src, self.path)

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_copy_main(self):
        dest = os.path.join(self.workdir, "another_symlink.txt")
        fi = FileInfoFactory().create(self.path)

        SymlinkOperations.copy_main(fi, dest)
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.islink(dest))

    def test_copy_main__link(self):
        SymlinkOperations.link_instead_of_copy = True

        dest = os.path.join(self.workdir, "another_symlink.txt")
        fi = FileInfoFactory().create(self.path)

        SymlinkOperations.copy_main(fi, dest)
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.islink(dest))

        SymlinkOperations.link_instead_of_copy = False

    def test_create(self):
        dest = self.path

        fi = SymlinkInfo(dest, create=True)
        os.remove(dest)  # remove to create

        SymlinkOperations.create(fi, dest)
        self.assertTrue(os.path.exists(dest))
        self.assertTrue(os.path.islink(dest))


# vim:sw=4 ts=4 et:
