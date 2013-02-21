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

import pmaker.models.FileObjects as FO
import pmaker.tenjinwrapper as TW

import bunch as B
import os.path
import unittest


def tmplpath(fname):
    return os.path.abspath(
        os.path.join(selfdir(), "../../templates/1/common/debian", fname)
    )


class Test_templates_1_common_debian(unittest.TestCase):

    def test__compat(self):
        tmpl = tmplpath("compat")

        # Template and generated output from it should equals.
        c = TW.template_compile(tmpl, {})
        c_ref = open(tmpl).read()

        self.assertEquals(c, c_ref)

    def test__rules(self):
        tmpl = tmplpath("rules")

        c = TW.template_compile(tmpl, {})
        c_ref = open(tmpl).read()

        self.assertEquals(c, c_ref)

    def test__changelog__wo_content(self):
        tmpl = tmplpath("changelog")
        context = dict(
            name="foobar",
            pversion="0.0.2",
            packager="John Doe",
            email="jdoe@example.com",
            date=Bunch(date="2011-11-10 20:03"),
        )

        c = TW.template_compile(tmpl, context)
        self.assertNotEquals(c, "")

    def test__changelog__w_content(self):
        tmpl = tmplpath("changelog")

        c_ref = open(
            os.path.join(
                os.path.dirname(__file__), "debian_changelog_example_00"
            )
        ).read()

        c = TW.template_compile(tmpl, {"changelog": c_ref})
        self.assertEquals(c, c_ref)

    def test__copyright(self):
        tmpl = tmplpath("copyright")
        context = dict(
            packager="John Doe",
            email="jdoe@example.com",
            date=Bunch(date="2011-11-10 20:03"),
            license="MIT",
        )

        c = TW.template_compile(tmpl, context)
        self.assertNotEquals(c, "")

    def test__dirs(self):
        tmpl = tmplpath("dirs")
        files = [
            FO.DirObject("/a/b/c"),
            FO.FileObject("/a/b/c/x"),
            FO.DirObject("/d/e"),
            FO.FileObject("/d/e/y"),
            FO.DirObject("/f/g/h/i"),
            FO.SymlinkObject("/f/g/h/i/j", "/a/b/c/x"),
        ]

        c = TW.template_compile(tmpl, {"files": files})
        self.assertNotEquals(c, "")

        #with open("/tmp/test.out", "w") as f:
        #    f.write(c)


# vim:sw=4:ts=4:et:
