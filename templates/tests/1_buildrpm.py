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
from pmaker.tests.common import selfdir

import pmaker.backend.tests.common as BTC
import pmaker.tenjinwrapper as TW
import bunch as B
import os.path
import random
import unittest


def tmplpath(fname):
    return os.path.abspath(
        os.path.join(selfdir(), "../../templates/1/buildrpm", fname)
    )


class Test_templates_1_buildrpm(unittest.TestCase):

    def test__package_spec(self):
        filelist = os.path.join(
            selfdir(), "config_example_01.json"
        )
        args = "-n foo -C " + filelist
        pkgdata = BTC.init_pkgdata(args)

        # TODO:
        pkgdata.relations = []
        context = pkgdata

        tmpl = tmplpath("package.spec")

        c = TW.template_compile(tmpl, context)
        self.assertNotEquals(c, "")


# vim:sw=4:ts=4:et:
