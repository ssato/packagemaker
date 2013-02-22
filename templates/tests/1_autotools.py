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

import pmaker.environ as E
import pmaker.tenjinwrapper as TW
import bunch as B
import os.path
import unittest


def tmplpath(fname):
    return os.path.abspath(
        os.path.join(selfdir(), "../../templates/1/autotools", fname)
    )


class Test_templates_1_autotools(unittest.TestCase):

    def test__00_rpm_mk(self):
        tmpl = tmplpath("rpm.mk")

        c = TW.template_compile(tmpl, {})
        c_ref = open(tmpl).read()

        self.assertEquals(c, c_ref)

    def test__01_package_spec(self):
        tmpl = tmplpath("package.spec")

        context = dict(
            name="foobarbaz",
            pversion="2.1.0",
            release="0.0.1",
            summary="pmaker RPM package example",
            group="Application/Text",
            license="GPLv3+",
            url="http://www.example.com/git/foobarbaz",
            compressor=B.Bunch(ext="xz", ),
            arch=False,
            hostname=E.hostname(),
            packager=E.get_fullname(),
            email=E.get_email(),
            date=B.Bunch(date="dummy date", timestamp="dummy timestamp"),
            files=[],
            conflicts=B.Bunch(files=[],),
            not_conflicts=B.Bunch(files=[],),
            relations=[],
            trigger=False,
        )

        c = TW.template_compile(tmpl, context)


# vim:sw=4:ts=4:et:
