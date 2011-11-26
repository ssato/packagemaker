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
from pmaker.models.Bunch import Bunch

import pmaker.models.FileObjects as FO
import pmaker.tenjinwrapper as TW
import os.path
import random
import unittest


def tmplpath(fname):
    return os.path.abspath(
        os.path.join(selfdir(), "../../templates/1/autotools.single", fname)
    )


class Test_templates_1_autotools_single(unittest.TestCase):

    def test__Makefile_am(self):
        tmpl = tmplpath("Makefile.am")

        paths = ["/a/b/c", "/a/b/d", "/a/e/f", "/a/g/h/i/j", "/x/y/z"]

        files = [FO.FileObject(p) for p in random.sample(paths, 3)] + \
            [FO.DirObject(p) for p in random.sample(paths, 3)] + \
            [FO.SymlinkObject(p, p) for p in random.sample(paths, 3)]

        distdata = [
            Bunch(id=i, files=random.sample(paths, 3), dir="/a/b") \
                for i in range(5)
        ]

        context = dict(
            conflicted_fileinfos=[1, 2, 3],  # dummy
            name="foobar",
            format="rpm",
            distdata=distdata,
            files=files,
        )

        c = TW.template_compile(tmpl, context)
        self.assertNotEquals(c, "")

    def test__configure_ac(self):
        tmpl = tmplpath("configure.ac")

        context = dict(
            name="foobar",
            pversion="0.0.1",
            compressor=Bunch(am_opt="dist-xz", ),
        )

        c = TW.template_compile(tmpl, context)
        self.assertNotEquals(c, "")

        #with open("/tmp/test.out", "w") as f:
        #    f.write(c)


# vim:sw=4 ts=4 et:
