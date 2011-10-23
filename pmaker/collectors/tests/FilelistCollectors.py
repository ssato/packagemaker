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
from pmaker.collectors.FilelistCollectors import FilelistCollector, \
    AnyFilelistCollector
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.configurations as C
import pmaker.options as O

import os.path
import unittest


def init_config(listfile):
    o = O.Options()
    (opts, args) = o.parse_args(["-n", "foo", listfile])
    return opts


class Test_00_FilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_00__init__(self):
        listfile = "/a/b/c/path.conf"  # dummy
        config = init_config(listfile)

        collector = FilelistCollector(listfile, config)

        self.assertTrue(isinstance(collector, FilelistCollector))
        self.assertEquals(collector.listfile, listfile)

    def test_01__parse__none(self):
        listfile = os.path.join(self.workdir, "files.list")
        config = init_config(listfile)

        line = "# this is a comment line to be ignored\n"

        collector = FilelistCollector(listfile, config)
        fos = collector._parse(line)

        self.assertEquals(fos, [])


# vim:sw=4 ts=4 et: