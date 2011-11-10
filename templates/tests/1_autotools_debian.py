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
        os.path.join(selfdir(), "../../templates/1/autotools/debian", fname)
    )


class Test_templates_1_autotools_debian(unittest.TestCase):

    def test__control(self):
        tmpl = tmplpath("control")

        context = dict(
            name="foobar",
            packager="John Doe",
            email="jdoe@example.com",
            url="http://www.example.com/git/foobar.git",
            noarch=True,
            relations=[
                Bunch(targets=["abc", "defg"], type="Depends"),
                Bunch(targets=["hi", "jklmn"], type="Depends"),
                Bunch(targets=["stu", "xyz"], type="Suggests"),
            ],
            summary="Debian package example",
        )

        c = TW.template_compile(tmpl, context)
        self.assertNotEquals(c, "")

        with open("/tmp/test.out", "w") as f:
            f.write(c)


# vim:sw=4 ts=4 et:
