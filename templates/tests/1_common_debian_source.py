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


def tmplpath(fname):
    return os.path.abspath(
        os.path.join(
            selfdir(),
            "../../templates/1/common/debian/source",
            fname,
        )
    )


class Test_templates_1_common_debian_source(unittest.TestCase):

    def test__format(self):
        tmpl = tmplpath("format")

        c = TW.template_compile(tmpl, {})
        c_ref = open(tmpl).read()

        self.assertEquals(c, c_ref)

    def test__options(self):
        tmpl = tmplpath("options")

        c = TW.template_compile(tmpl, {})
        c_ref = open(tmpl).read()

        self.assertEquals(c, c_ref)


# vim:sw=4:ts=4:et:
