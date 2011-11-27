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
from pmaker.models.RpmFileInfoFactory import RpmFileInfoFactory

import os.path
import sys
import unittest


class TestRpmFileInfoFactory(unittest.TestCase):

    _multiprocess_can_split_ = True

    def helper_00(self, filepath):
        if not os.path.exists("/var/lib/rpm/Basenames"):
            logging.info("rpmdb does not look exists. skip this test.")
            return False

        if not os.path.exists(filepath):
            print >> sys.stderr, \
                "File %s does not look exists. skip this test." % filepath
            return False

        return True

    def test__stat(self):
        f = "/etc/hosts"

        if not self.helper_00(f):
            return

        (_mode, uid, gid) = RpmFileInfoFactory()._stat(f)

        self.assertEquals(uid, 0)
        self.assertEquals(gid, 0)

    def test__stat_call_parent_method(self):
        ps = (p for p in (".bashrc", ".zshrc", ".tcshrc"))

        for f in (os.path.expanduser("~/" + p) for p in ps):
            if os.path.exists(f):
                break

        if not self.helper_00(f):
            return

        (_mode, uid, gid) = RpmFileInfoFactory()._stat(f)

        self.assertEquals(uid, os.getuid())
        self.assertEquals(gid, os.getgid())


# vim:sw=4 ts=4 et:
