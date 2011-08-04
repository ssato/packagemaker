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
from pmaker.utils import *
from pmaker.globals import DATE_FMT_SIMPLE, DATE_FMT_RFC2822
from pmaker.tests.common import setup_workdir, cleanup_workdir

import copy
import doctest
import glob
import logging
import os
import random
import re
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



class Test_singleton(unittest.TestCase):

    def test_singleton(self):
        class A(object):
            pass

        A = singleton(A)

        a0 = A()
        a1 = A()

        self.assertTrue(a0 == a1)



class TestMemoized(unittest.TestCase):

    def test_memoized(self):
        """TODO: not implemented yet.
        """
        pass


class TestChecksum(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        (_, self.f) = tempfile.mkstemp(dir=self.workdir)
        open(self.f, "w").write(str(random.random()))

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_checksum_no_file(self):
        csum_ref = "0" * len(sha1("").hexdigest())
        self.assertEquals(checksum(), csum_ref)

    def test_checksum_permission_denied(self):
        if os.getuid() == 0:
            print >> sys.stderr, "You look root and cannot test this. Skipped"
            return

        path = random.choice(
            [p for p in ("/etc/at.deny", "/etc/securetty", "/etc/sudoer", "/etc/shadow") \
                if os.path.exists(p) and not os.access(p, os.R_OK)]
        )

        csum_ref = "0" * len(sha1("").hexdigest())
        self.assertEquals(checksum(path), csum_ref)

    def test_checksum(self):
        csum_ref = subprocess.check_output("sha1sum " + self.f, shell=True).split()[0]
        self.assertEquals(checksum(self.f), csum_ref)



class Test_st_mode_to_mode(unittest.TestCase):

    def test_st_mode_to_mode(self):
        file0 = "/etc/resolv.conf"
        if os.path.exists(file0):
            mode = os.lstat(file0).st_mode
            expected = oct(stat.S_IMODE(mode & 0777))
            self.assertEquals(expected, st_mode_to_mode(mode))

    def test_st_mode_to_mode__special(self):
        gshadow = "/etc/gshadow-"
        if os.path.exists(gshadow):
            mode = os.lstat(gshadow).st_mode
            self.assertEquals("0000", st_mode_to_mode(mode))



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

    def test_unique_num_lists(self):
        self.assertListEqual(unique([0, 3, 1, 2, 1, 0, 4, 5]), [0, 1, 2, 3, 4, 5])

    def test_unique_str_list(self):
        self.assertListEqual(unique(c for c in "dagcbfefagb"), ["a", "b", "c", "d", "e", "f", "g"])



NULL_DICT = dict()


class Test_dicts_comp(unittest.TestCase):

    def test_dicts_comp__null_vs_null(self):
        self.assertTrue(dicts_comp(NULL_DICT, NULL_DICT))

    def test_dicts_comp__not_null_vs_null(self):
        self.assertFalse(dicts_comp({"a": 1}, NULL_DICT))

    def test_dicts_comp__same_values(self):
        d0 = dict(a=0, b=1, c=2)
        d1 = copy.copy(d0)
        self.assertTrue(dicts_comp(d0, d1))

    def test_dicts_comp__rhs_has_more_kvs(self):
        d0 = dict(a=0, b=1, c=2)
        d1 = copy.copy(d0)
        d1["d"] = 3
        self.assertTrue(dicts_comp(d0, d1))

    def test_dicts_comp__by_key(self):
        d0 = dict(a=0, b=1, c=2)
        d1 = dict(a=0, b=1, c=2, d=3)
        self.assertFalse(dicts_comp(d0, d1, ("d")))

    def test_dicts_comp__by_key(self):
        d0 = dict(a=0, b=1, c=2)
        d1 = dict(a=0, b=1, c=2, d=3)
        self.assertTrue(dicts_comp(d0, d1, ("a", "b")))



class Test_listplus(unittest.TestCase):

    def test_listplus(self):
        self.assertTrue(isinstance(listplus([0], (i for i in range(10))), list))



class Test_true(unittest.TestCase):

    def test_true(self):
        self.assertTrue(true(False))



class Test_true(unittest.TestCase):

    def test_true(self):
        self.assertTrue(true(False))



class Test_date(unittest.TestCase):

    def test_date__default(self):
        self.assertNotEquals(re.match(r".{3} .{3} +\d+ \d{4}", date()), None)

    def test_date__simple(self):
        self.assertNotEquals(re.match(r"\d{8}", date(DATE_FMT_SIMPLE)), None)

    def test_date__rfc2822(self):
        self.assertNotEquals(
            re.match(r".{3}, \d{1,2} .* \d{4} \d{2}:\d{2}:\d{2} \+\d{4}", date(DATE_FMT_RFC2822)),
            None
        )



class Test_do_nothing(unittest.TestCase):

    def test_do_nothing(self):
        do_nothing()



class Test_on_debug_mode(unittest.TestCase):

    def test_on_debug_mode__debug(self):
        logging.getLogger().setLevel(logging.DEBUG)
        self.assertTrue(on_debug_mode())

    def test_on_debug_mode__info(self):
        logging.getLogger().setLevel(logging.INFO)
        self.assertFalse(on_debug_mode())



class Test_rm_rf_and_createdir(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_createdir_and_rm_rf__simple(self):
        path = os.path.join(self.workdir, "a")

        createdir(path)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isdir(path))

        rm_rf(path)
        self.assertFalse(os.path.exists(path))

        rm_rf(path)

    def test_createdir_and_rm_rf__multi(self):
        topdir = os.path.join(self.workdir, "a")

        for c in "bc":
            p = os.path.join(topdir, c)
            createdir(p)

            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.isdir(p))

        p = os.path.join(topdir, "d", "e")
        createdir(p)
        self.assertTrue(os.path.exists(p))
        self.assertTrue(os.path.isdir(p))

        open(os.path.join(topdir, "x"), "w").write("test\n")
        open(os.path.join(topdir, "b", "y"), "w").write("test2\n")
        open(os.path.join(topdir, "d", "e", "z"), "w").write("test3\n")

        rm_rf(topdir)
        self.assertFalse(os.path.exists(topdir))



class Test_find_template(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        self.template = os.path.join(self.workdir, "a.tmpl")

        open(self.template, "w").write("$a\n")

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_find_template__None(self):
        tmpl = find_template("not_exist.tmpl")

        self.assertTrue(tmpl is None)

    def test_find_template__exact_path(self):
        tmpl = find_template(self.template)

        self.assertTrue(tmpl is not None)

    def test_find_template__search_paths(self):
        tmplname = os.path.basename(self.template)
        tmpl = find_template(tmplname, [self.workdir])

        self.assertTrue(tmpl is not None)



class Test_compile_template(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_compile_template__str(self):
        tmpl_s = "a=$a b=$b"
        params = {"a": 1, "b": "b"}

        self.assertEquals("a=1 b=b", compile_template(tmpl_s, params))

    def test_compile_template__file(self):
        tmpl = os.path.join(self.workdir, "test.tmpl")
        open(tmpl, "w").write("a=$a b=$b")

        params = {"a": 1, "b": "b"}

        self.assertEquals("a=1 b=b", compile_template(tmpl, params, is_file=True))



class Test_sort_out_paths_by_dir(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_sort_out_paths_by_dir(self):
        path_list = [
           "/etc/resolv.conf",
           "/etc/sysconfig/iptables",
           "/etc/sysconfig/networks",
        ]

        expected_result = [
            dict(dir="/etc", files=["/etc/resolv.conf"], id="0"),
            dict(dir="/etc/sysconfig",
                files=["/etc/sysconfig/iptables", "/etc/sysconfig/networks"],
                id="1"),
        ]
        for i, d in enumerate(sort_out_paths_by_dir(path_list)):
            self.assertTrue(dicts_comp(d, expected_result[i]))



class Test_cache_needs_updates_p(unittest.TestCase):

    def test_cache_needs_updates_p(self):
        """TODO: Implement this.
        """


class Test_parse_conf_value(unittest.TestCase):

    def test_parse_conf_value(self):
        self.assertEquals(0, parse_conf_value("0"))
        self.assertEquals(123, parse_conf_value("123"))
        self.assertEquals(True, parse_conf_value("True"))
        self.assertEquals([1,2,3], parse_conf_value("[1,2,3]"))
        self.assertEquals("a string", parse_conf_value("a string"))
        self.assertEquals("0.1", parse_conf_value("0.1"))
        self.assertEquals("%config", parse_conf_value("'%config'"))


# vim: set sw=4 ts=4 et:
