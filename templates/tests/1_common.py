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
from pmaker.globals import CONFLICTS_NEWDIR, CONFLICTS_SAVEDIR
from pmaker.tests.common import selfdir

import pmaker.models.FileObjects as FO
import pmaker.tenjinwrapper as TW

import bunch as B
import os.path
import random
import unittest


def tmplpath(fname):
    return os.path.abspath(
        os.path.join(selfdir(), "../../templates/1/common", fname)
    )


class Test_templates_1_common(unittest.TestCase):

    def test__README(self):
        tmpl = tmplpath("README")

        d = Bunch(date="2011.11.10")

        context = dict(
            hostname="foobar.example.com",
            packager="John Doe",
            date=d,
        )

        # TBD:
        c = TW.template_compile(tmpl, context)
        self.assertTrue(c != "")

        #c_ref = open(tmpl).read()
        #self.assertEquals(c, c_ref)

    def test__manifest(self):
        tmpl = tmplpath("manifest")

        context = dict(
            not_conflicts=Bunch(
                files=[
                    Bunch(install_path=p) for p in ["/a/b/c", "/w/x/y/z"]
                ]
            ),
        )
        c_ref = """\
/a/b/c
/w/x/y/z
"""

        c = TW.template_compile(tmpl, context)
        self.assertEquals(c, c_ref)

    def test__manifest_overrides(self):
        tmpl = tmplpath("manifest.overrides")

        context = dict(
            conflicts=Bunch(
                files=[
                    Bunch(install_path=p) for p in ["/a/b/c", "/w/x/y/z"]
                ]
            ),
        )
        c_ref = """\
/a/b/c
/w/x/y/z
"""

        c = TW.template_compile(tmpl, context)
        self.assertEquals(c, c_ref)

    def test__apply_overrides(self):
        tmpl = tmplpath("apply-overrides")

        paths = ["/a/b/c", "/a/b/d", "/a/e/f", "/a/g/h/i/j", "/x/y/z"]

        def g(f, paths=paths):
            f.original_path = random.choice(paths)
            return f

        files = [g(FO.FileObject(p)) for p in random.sample(paths, 4)]

        context = dict(
            conflicts=Bunch(
                files=files,
                savedir=CONFLICTS_SAVEDIR % {"name": "foo"},
                newdir=CONFLICTS_NEWDIR % {"name": "foo"},
            )
        )

        # TBD:
        c = TW.template_compile(tmpl, context)
        self.assertTrue(c != "")

    def test__apply_overrides__wo_conflicts(self):
        tmpl = tmplpath("apply-overrides")

        context = dict(
            conflicts=Bunch(
                files=[],
                savedir=CONFLICTS_SAVEDIR % {"name": "foo"},
                newdir=CONFLICTS_NEWDIR % {"name": "foo"},
            )
        )

        c = TW.template_compile(tmpl, context)
        c_ref = """\
#! /bin/bash
set -e

# No conflicts and nothing to do:
exit 0
"""
        self.assertEquals(c, c_ref)

        ## for debug:
        #with open("/tmp/test.out", "w") as f:
        #    f.write(c)

    def test__revert_overrides(self):
        tmpl = tmplpath("revert-overrides")

        paths = ["/a/b/c", "/a/b/d", "/a/e/f", "/a/g/h/i/j", "/x/y/z"]

        def g(f, paths=paths):
            f.original_path = random.choice(paths)
            return f

        files = [g(FO.FileObject(p)) for p in random.sample(paths, 4)]

        context = dict(
            conflicts=Bunch(
                files=files,
                savedir=CONFLICTS_SAVEDIR % {"name": "foo"},
                newdir=CONFLICTS_NEWDIR % {"name": "foo"},
            )
        )

        # TBD:
        c = TW.template_compile(tmpl, context)
        self.assertTrue(c != "")

    def test__revert_overrides__wo_conflicts(self):
        tmpl = tmplpath("revert-overrides")

        context = dict(
            conflicts=Bunch(
                files=[],
                savedir=CONFLICTS_SAVEDIR % {"name": "foo"},
                newdir=CONFLICTS_NEWDIR % {"name": "foo"},
            )
        )

        c = TW.template_compile(tmpl, context)
        c_ref = """\
#! /bin/bash
set -e

# No conflicts and nothing to do:
exit 0
"""
        self.assertEquals(c, c_ref)


# vim:sw=4:ts=4:et:
