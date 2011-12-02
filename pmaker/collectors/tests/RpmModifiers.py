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
from pmaker.collectors.RpmModifiers import *

from pmaker.models.FileInfoFactory import FileInfoFactory

import pmaker.models.FileObjectFactory as F
import pmaker.utils as U

import os.path
import unittest


#F = FileInfoFactory()


class Test_00_RpmAttributeModifier(unittest.TestCase):

    def test_update(self):
        modifier = RpmAttributeModifier()

        f = F.create("/bin/bash")
        new_f = modifier.update(f)

        self.assertTrue(getattr(new_f, "rpm_attr", False))


class Test_01_RpmConflictsModifier(unittest.TestCase):

    def setUp(self):
        pname = "foo"
        self.modifier = RpmConflictsModifier(pname)
        (self.savedir, self.newdir) = U.conflicts_dirs(pname)

    def test_01__init__conflicts(self):
        self.assertEquals(self.modifier.savedir, self.savedir)
        self.assertEquals(self.modifier.newdir, self.newdir)

        owner = self.modifier.find_owner("/bin/bash")
        self.assertEquals(owner["name"], "bash")

    def test_02_update(self):
        f = F.create("/bin/bash")
        new_f = self.modifier.update(f)

        self.assertNotEquals(new_f.original_path, f.install_path)

        #path = fileinfo.target[1:]  # strip "/" at the head.
        #fileinfo.target = os.path.join(self.newdir, path)
        #fileinfo.save_path = os.path.join(self.savedir, path)


# vim:sw=4 ts=4 et:
