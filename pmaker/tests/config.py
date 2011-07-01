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
from pmaker.config import *
from pmaker.utils import rm_rf

import optparse
import os
import os.path
import sys
import tempfile
import unittest



class TestConfig(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        conf = """\
[DEFAULT]
a: aaa
b: bbb

[profile0]
a: xxx
b: yyy
"""
        path = os.path.join(self.workdir, "config")
        open(path, "w").write(conf)

        self.paths = [path]

    def tearDown(self):
        rm_rf(self.workdir)

    def test_list_paths__None(self):
        prog = "testapp"
        home = os.environ.get("HOME", os.curdir)

        paths = [
            "/etc/%s.conf" % prog,
            os.path.join(home, ".config", prog),
            os.environ.get("%sRC" % prog.upper(), os.path.join(home, ".%src" % prog))
        ]

        self.assertEquals(paths, Config._list_paths(prog, None))
 
    def test_list_paths__not_None(self):
        self.assertEquals(["/a/b/c"], Config._list_paths("testapp", ["/a/b/c"]))

    def test__load__default(self):
        params = Config._load(self.paths, profile=None)

        self.assertEquals(params["a"], "aaa")
        self.assertEquals(params["b"], "bbb")

    def test__load__with_profile(self):
        params = Config._load(self.paths, profile="profile0")

        self.assertEquals(params["a"], "xxx")
        self.assertEquals(params["b"], "yyy")

    def test__init__(self):
        config = Config(paths=self.paths)

    def test_defaults(self):
        defaults = Config.defaults()

        self.assertTrue(isinstance(defaults, dict))
        self.assertTrue(defaults.keys() > 0)

    def test_as_dict(self):
        config = Config(paths=self.paths)
        config.as_dict()



class Test_parse_list_str(unittest.TestCase):

    def test_no_arg(self):
        self.assertEquals(parse_list_str(""), [])

    def test_single_arg(self):
        self.assertEquals(parse_list_str("a,b"), ["a", "b"])

    def test_multi_args(self):
        self.assertEquals(parse_list_str("a,b,c,"), ["a", "b", "c"])



class Test_parse_relations(unittest.TestCase):

    def test_relations_str(self):
        self.assertEquals(
            parse_relations("requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old"),
            [('requires', ['bash', 'zsh']), ('obsoletes', ['sysdata']), ('conflicts', ['sysdata-old'])]
        )

    def test_relations_str__invalid_args(self):
        self.assertEquals(
            parse_relations("requires:,zsh;;obsoletes:;conflicts:sysdata-old,"),
            [('requires', ['zsh']), ('conflicts', ['sysdata-old'])]
        )



class Test_x_defaults(unittest.TestCase):

    def test_upto_defaults(self):
        defaults = upto_defaults()

        self.assertTrue(bool(defaults["choices"]))

    def test_driver_defaults(self):
        defaults = driver_defaults()

        self.assertTrue(bool(defaults["choices"]))

    def test_itype_defaults(self):
        defaults = itype_defaults()

        self.assertTrue(bool(defaults["choices"]))

    def test_compressor_defaults(self):
        defaults = compressor_defaults()

        self.assertTrue(bool(defaults["choices"]))



class Test_relations_option_parser(unittest.TestCase):

    def setUp(self):
        defaults = relations_defaults()

        p = optparse.OptionParser()
        p.add_option("", "--relations", **defaults)

        self.parser = p
        self.defaults = defaults

    def parse_args(self, args):
        return self.parser.parse_args(args.split())

    def test_default(self):
        """test_default: Cases that this option not given"""
        (options, _) = self.parse_args("")

        self.assertEquals(options.relations, self.defaults["default"])

    def test_set(self):
        (options, _) = self.parse_args("--relations requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old")
        expected = [
            ('requires', ['bash', 'zsh']),
            ('obsoletes', ['sysdata']),
            ('conflicts', ['sysdata-old']),
        ]

        d = dict(options.relations)
        d_ref = dict(expected)

        self.assertEquals(d["requires"], d_ref["requires"])
        self.assertEquals(d["obsoletes"], d_ref["obsoletes"])
        self.assertEquals(d["conflicts"], d_ref["conflicts"])



class Test_parse_args(unittest.TestCase):

    def test__min(self):
        (parser, options, args) = parse_args("-n foo".split())

        self.assertTrue(isinstance(parser, optparse.OptionParser))
        self.assertTrue(isinstance(options, optparse.Values))


# vim: set sw=4 ts=4 expandtab:
