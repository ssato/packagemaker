#
# Copyright (C) 2011 Satoru SATOH <ssato at redhat.com>
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
from pmaker.tests.common import selfdir

import pmaker.tenjinwrapper as TW
import os.path
import unittest


class Test_00(unittest.TestCase):

    def test_00_template_compile(self):
        template_path = os.path.join(selfdir(), "template_example_00.tmpl")

        c0 = TW.template_compile(template_path, {})
        c1 = TW.template_compile(template_path,
            {"title": "pyTenjin tests: context", }
        )

        # TBD:
        self.assertTrue(bool(c0))
        self.assertTrue(bool(c1))


# vim:sw=4 ts=4 et:
