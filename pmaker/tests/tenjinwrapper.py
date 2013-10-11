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
from pmaker.tests.common import selfdir, setup_workdir, cleanup_workdir

import pmaker.tenjinwrapper as TT
import os.path
import unittest


class Test_00(unittest.TestCase):

    def test_00_template_compile(self):
        template_path = os.path.join(selfdir(), "template_example_00.tmpl")

        c0 = TT.compile(template_path, {})
        c1 = TT.compile(template_path, {"title": "pyTenjin tests: context", })

        # TBD:
        self.assertTrue(bool(c0))
        self.assertTrue(bool(c1))


class Test_10(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        self.template = os.path.join(self.workdir, "a.tmpl")

        open(self.template, "w").write("$a\n")

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_00_find_template__None(self):
        with self.assertRaises(TT.TemplateNotFoundError):
            tmpl = TT.find_template("not_exist.tmpl", ask=False)

    def test_10_find_template__exact_path(self):
        tmpl = TT.find_template(self.template)
        self.assertTrue(tmpl is not None)

    def test_20_find_template__search_paths(self):
        tmplname = os.path.basename(self.template)
        tmpl = TT.find_template(tmplname, [self.workdir])
        self.assertTrue(tmpl is not None)

# vim:sw=4:ts=4:et:
