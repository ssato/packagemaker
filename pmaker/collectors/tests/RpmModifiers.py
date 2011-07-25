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
from pmaker.globals import *
from pmaker.collectors.RpmModifiers import *
from pmaker.models.FileInfoFactory import *

import unittest
import os.path



FACTORY = FileInfoFactory()


class TestRpmAttributeModifier(unittest.TestCase):

    def setUp(self):
        self.modifier = RpmAttributeModifier()

    def test_update(self):
        fi = FACTORY.create("/bin/bash")
        new_fi = self.modifier.update(fi)

        self.assertTrue(getattr(new_fi, "rpm_attr", False))



class TestRpmConflictsModifier(unittest.TestCase):

    def setUp(self):
        pname = "foo"
        self.modifier = RpmConflictsModifier(pname)
        self.savedir = CONFLICTS_SAVEDIR % {"name": pname}
        self.newdir = CONFLICTS_NEWDIR % {"name": pname}

    def test__init__conflicts(self):
        self.assertEquals(self.modifier.savedir, self.savedir)
        self.assertEquals(self.modifier.newdir, self.newdir)

        owner = self.modifier.find_owner("/bin/bash")
        self.assertEquals(owner["name"], "bash")

    def test_update(self):
        fi = FACTORY.create("/bin/bash")
        new_fi = self.modifier.update(fi)

        self.assertNotEquals(new_fi.original_path, fi.install_path)

        #path = fileinfo.target[1:]  # strip "/" at the head.
        #fileinfo.target = os.path.join(self.newdir, path)
        #fileinfo.save_path = os.path.join(self.savedir, path)


# vim: set sw=4 ts=4 expandtab:
