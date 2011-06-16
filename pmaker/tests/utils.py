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
#

from pmaker.utils import *

import doctest
import os
import random
import subprocess
import tempfile
import unittest



class TestMemoize(unittest.TestCase):

    def test_memoize(self):
        x = 0
        f = lambda _x: x

        f = memoize(f)
        x = 1

        self.assertEquals(f(0), f(1))


class TestMemoized(unittest.TestCase):

    def test_memoized(self):
        pass


class TestChecksum(unittest.TestCase):

    def setUp(self):
        (_, self.f) = tempfile.mkstemp()
        open(self.f, "w").write(str(random.random()))

    def tearDown(self):
        os.remove(self.f)

    def test_checksum_no_file(self):
        csum_ref = "0" * len(sha1("").hexdigest())
        self.assertEquals(checksum(), csum_ref)

    def test_checksum(self):
        csum_ref = subprocess.check_output("sha1sum " + self.f, shell=True).split()[0]
        self.assertEquals(checksum(self.f), csum_ref)



class TestIsFoldable(unittest.TestCase):

    def test_is_foldable_empty(self):
        self.assertTrue(is_foldable([]))
        self.assertTrue(is_foldable(()))

    def test_is_foldable_generator_expression(self):
        self.assertTrue(is_foldable(x for x in range(3)))

    def test_is_foldable_primitives(self):
        self.assertFalse(is_foldable(None))
        self.assertFalse(is_foldable(True))
        self.assertFalse(is_foldable(1))



class TestFlatten(unittest.TestCase):

    def test_flatten_empty(self):
        self.assertListEqual(flatten([]), [])

    def test_flatten_lists(self):
        self.assertListEqual(flatten([[1, 2, 3], [4, 5]]), [1, 2, 3, 4, 5])
        self.assertListEqual(flatten([[1, 2, [3]], [4, [5, 6]]]), [1, 2, 3, 4, 5, 6])
        self.assertListEqual(flatten([(1, 2, 3), (4, 5)]), [1, 2, 3, 4, 5])

    def test_flatten_generator_expression(self):
        self.assertListEqual(flatten((i, i * 2) for i in range(5)), [0, 0, 1, 2, 2, 4, 3, 6, 4, 8])



class TestConcat(unittest.TestCase):

    def test_concat_empty(self):
        self.assertListEqual(concat([[]]), [])
        self.assertListEqual(concat((())), [])

    def test_concat_lists(self):
        self.assertListEqual(concat([[1, 2, 3], [4, 5]]), [1, 2, 3, 4, 5])
        self.assertListEqual(concat([[1, 2, [3]], [4, [5, 6]]]), [1, 2, [3], 4, [5, 6]])
        self.assertListEqual(concat([(1, 2, [3]), (4, [5, 6])]), [1, 2, [3], 4, [5, 6]])

    def test_concat_generator_expression(self):
        self.assertListEqual(concat((i, i * 2) for i in range(5)), [0, 0, 1, 2, 2, 4, 3, 6, 4, 8])


class TestUnique(unittest.TestCase):

    def test_unique_empty(self):
        self.assertListEqual(unique([]), [])

    def test_unique_lists(self):
        self.assertListEqual(unique([0, 3, 1, 2, 1, 0, 4, 5]), [0, 1, 2, 3, 4, 5])


# vim: set sw=4 ts=4 et:
