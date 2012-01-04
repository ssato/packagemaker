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
        os.path.join(selfdir(), "../../templates/1/rpmspec", fname)
    )


class Test_00(unittest.TestCase):

    def test_01_package_spec(self):
        tmpl = tmplpath("perl/package.spec")

        context = dict(
            name="perl-foo-bar-baz",
            version="1.0",
            license="Perl",
            summary="Perl foo bar baz library",
        )

        c = TW.template_compile(tmpl, context)


# vim:sw=4 ts=4 et:
