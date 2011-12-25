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
from pmaker.models.FileObjects import FileObject, UnknownObject
from pmaker.utils import checksum

import pmaker.models.FileObjectFactory as Factory

import glob
import os
import os.path
import pwd
import random
import unittest


class TestUnsupportedTypesFilter(unittest.TestCase):

    def setUp(self):
        self.filter = UnsupportedTypesFilter()

    def test_pred__supported(self):
        fo = FileObject("/dummy/path", 33204, 0, 0, checksum(), dict())
        self.assertFalse(self.filter.pred(fo))

    def test_pred__unsupported(self):
        fo = UnknownObject("/dummy/path")
        self.assertTrue(self.filter.pred(fo))

    def test_pred__supported__fileobjects(self):
        paths = [
            "/etc/resolv.conf", "/etc/hosts",  # normal files
            "/etc",  # dirs
            "/etc/rc",  "/etc/init.d", "/etc/grub.conf"  # symlinks
        ]
        paths = [p for p in paths if os.path.exists(p)]

        for p in paths:
            fo = Factory.create(p)
            self.assertFalse(self.filter.pred(fo))

    def test_pred__unsupported__fileobjects(self):
        username = pwd.getpwuid(os.getuid()).pw_name
        paths = [
            "/dev/null", "/dev/zero"  # device files
        ] + glob.glob("/tmp/orbit-%s/linc-*" % username)[:3]  # socket

        paths = [p for p in paths if os.path.exists(p)]

        for p in paths:
            fo = Factory.create(p)
            self.assertTrue(self.filter.pred(fo))


class TestNotExistFilter(unittest.TestCase):

    def test_pred__not_exist(self):
        filter = NotExistFilter()
        path = "/a/b/c"

        fo = Factory.create(path)
        self.assertTrue(filter.pred(fo))

    def test_pred__not_exist(self):
        filter = NotExistFilter()
        path = "/bin/sh"

        assert os.path.exists(path)

        fo = Factory.create(path)
        self.assertFalse(filter.pred(fo))


class TestReadAccessFilter(unittest.TestCase):

    def test_pred__not_permitted_to_read_or_to_be_created(self):
        if os.getuid() == 0:
            print >> sys.stderr, "You look root and cannot test this. Skipped"
            return

        filter = ReadAccessFilter()
        path = random.choice(
            [p for p in ("/etc/at.deny",
                         "/etc/securetty",
                         "/etc/sudoer",
                         "/etc/shadow",
                         "/etc/grub.conf") \
                if os.path.exists(p) and not os.access(p, os.R_OK)]
        )

        fo = Factory.create(path)

        self.assertTrue(filter.pred(fo))

        fo.create = True

        self.assertFalse(filter.pred(fo))

    def test_pred__permitted_to_read(self):
        filter = ReadAccessFilter()
        path = random.choice(
            [p for p in ("/etc/hosts",
                         "/etc/resolv.conf",
                         "/etc/sysctl.conf",
                    ) if os.path.exists(p) and os.access(p, os.R_OK)
            ]
        )

        fo = Factory.create(path)
        self.assertFalse(filter.pred(fo))


# vim:sw=4 ts=4 et:
