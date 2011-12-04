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
import tests.common as TC
import pmaker.environ as E
import pmaker.tests.common as C

import os.path
import unittest


class Test_00_autotools_single(unittest.TestCase):

    def setUp(self):
        (name, pversion) = ("foo", "0.0.3")

        (self.workdir, args) = TC.setup(
            ["--name", name, "--pversion", pversion]
        )
        self.listfile = os.path.join(self.workdir, "files.list")
        comp_ext = E.Env().compressor.extension

        self.args = args + ["--backend", "autotools.single.tgz", self.listfile]

        pn = "%s-%s" % (name, pversion)
        self.tgz = os.path.join(self.workdir, pn, pn + ".tar." + comp_ext)

    def tearDown(self):
        #C.cleanup_workdir(self.workdir)
        pass

    def test_00_generated_file(self):
        target = os.path.join(self.workdir, "aaa.txt")

        open(target, "w").write("\n")
        open(self.listfile, "w").write("%s\n" % target)

        TC.run_w_args(self.args, self.workdir)

        self.assertTrue(os.path.exists(self.tgz))

    def test_01_system_file(self):
        target = TC.get_random_system_files(1, "/etc/*")

        open(self.listfile, "w").write("%s\n" % target)

        TC.run_w_args(self.args, self.workdir)

        self.assertTrue(os.path.exists(self.tgz))


# vim:sw=4 ts=4 et:
