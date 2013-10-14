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
#from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.rpmspec.python as P

import re
import unittest


_BASEURL = "https://pypi.python.org/packages/source/"


class Test_00(unittest.TestCase):

    def test_get_download_url(self):
        n = "pyev"
        dp = re.compile(_BASEURL + "p/%s/%s-.*.tar.gz" % (n, n))
        u = P.get_download_url(n)

        self.assertTrue(dp.match(u))


# vim:sw=4:ts=4:et:
