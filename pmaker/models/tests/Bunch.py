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
from pmaker.models.Bunch import Bunch
from pmaker.tests.common import setup_workdir, cleanup_workdir

import cPickle as pickle
import os.path
import unittest


class TestBunch(unittest.TestCase):

    def test_create_set_and_get(self):
        name = "Bunch"
        category = "pattern"
        tags = ["a", "b", "c"]
        newkey = "newkey"

        bunch = Bunch(name=name, category=category, tags=tags)

        self.assertEquals(bunch.name, name)
        self.assertEquals(bunch.category, category)
        self.assertEquals(bunch.tags, tags)

        self.assertEquals(bunch["name"], name)
        self.assertEquals(bunch["category"], category)
        self.assertEquals(bunch["tags"], tags)

        self.assertFalse(newkey in bunch)

        bunch.newkey = True
        self.assertTrue(newkey in bunch)

        # TODO: The order of keys may be lost currently.
        #self.assertEquals(bunch.keys(), ("name", "category", "newkey"))


class TestBunch_pickle(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_pickle(self):
        name = "Bunch"
        tags = ["a", "b", "c"]

        bunch = Bunch(name=name, tags=tags)

        bf = os.path.join(self.workdir, "test.pkl")
        pickle.dump(bunch, open(bf, "wb"))

        bunch2 = pickle.load(open(bf, "rb"))

        self.assertEquals(bunch2.name, bunch.name)
        self.assertEquals(bunch2.tags, bunch.tags)

        self.assertEquals(bunch2["name"], bunch["name"])
        self.assertEquals(bunch2["tags"], bunch["tags"])

        self.assertEquals(str(bunch2), str(bunch))


# vim:sw=4 ts=4 et:
