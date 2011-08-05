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
from pmaker.models.FileInfo import FileInfo, UnknownInfo
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.utils import checksum

import os
import random
import unittest



class TestUnsupportedTypesFilter(unittest.TestCase):

    def setUp(self):
        self.filter = UnsupportedTypesFilter()

    def test_pred__supported(self):
        fi = FileInfo("/dummy/path", 33204, 0, 0, checksum(), dict())
        self.assertFalse(self.filter.pred(fi))

    def test_pred__unsupported(self):
        fi = UnknownInfo("/dummy/path")
        self.assertTrue(self.filter.pred(fi))



class TestReadAccessFilter(unittest.TestCase):

    def setUp(self):
        self.filter = ReadAccessFilter()
        path = random.choice(
            [p for p in ("/etc/at.deny", "/etc/securetty", "/etc/sudoer", "/etc/shadow", "/etc/grub.conf") \
                if os.path.exists(p) and not os.access(p, os.R_OK)]
        )
        self.fi = FileInfoFactory().create(path)

    def test_pred__dont_have_read_access(self):
        if os.getuid() == 0:
            print >> sys.stderr, "You look root and cannot test this. Skipped"
            return

        self.assertTrue(self.filter.pred(self.fi))


    def test_pred__dont_have_read_access_but_to_be_created(self):
        if os.getuid() == 0:
            print >> sys.stderr, "You look root and cannot test this. Skipped"
            return

        fi = self.fi; fi.create = True
        self.assertFalse(self.filter.pred(fi))

    def test_pred__have_read_access(self):
        path = random.choice(
            [p for p in ("/etc/hosts", "/etc/resolv.conf", "/etc/sysctl.conf") \
                if os.path.exists(p) and os.access(p, os.R_OK)]
        )

        fi = FileInfoFactory().create(path)
        self.assertFalse(self.filter.pred(fi))



# vim: set sw=4 ts=4 expandtab:
