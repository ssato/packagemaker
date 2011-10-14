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

import pmaker.anycfg as PA

import glob
import optparse
import os
import os.path
import pprint
import sys
import tempfile
import unittest


class Test__list_paths(unittest.TestCase):

    def test_list_paths__None(self):
        prog = "testapp"
        home = os.environ.get("HOME", os.curdir)

        paths = ["/etc/%s.conf" % prog]
        paths += sorted(glob.glob("/etc/%s.d/*.conf" % prog))
        paths += [os.path.join(home, ".config", prog)]
        paths += [
            os.environ.get("%sRC" % prog.upper(), os.path.join(home, ".%src" % prog))
        ]

        paths_r = PA.list_paths(prog, None)

        for p in paths:
            self.assertTrue(p in paths_r,
                "Expected %s in %s" % (p, str(paths_r)))

    def test_list_paths__not_None(self):
        self.assertEquals(["/a/b/c"], PA.list_paths("testapp", ["/a/b/c"]))


class TestIniConfigParser(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

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
        self.config = Bunch(
            defaults=Bunch(a="aaa", b="bbb"),
            profile0=Bunch(a="xxx", b="yyy"),
        )

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test__load(self):
        parser = PA.IniConfigParser("testapp")
        config = parser.load(self.paths[0])

        for k, v in config.defaults.iteritems():
            self.assertEquals(self.config.defaults[k], v)

        for k, v in config.profile0.iteritems():
            self.assertEquals(self.config.profile0[k], v)


if PA.json is not None: 

    class TestJsonConfigParser(unittest.TestCase):

        def setUp(self):
            self.workdir = setup_workdir()

            conf = """\
{
    "defaults": {
        "a": "aaa",
        "b": "bbb"
    },
    "profile0": {
        "a": "xxx",
        "b": "yyy"
    },
    "array0": [1, 2, 3]
}
"""
            path = os.path.join(self.workdir, "config.json")
            open(path, "w").write(conf)

            self.paths = [path]
            self.config = Bunch(
                defaults=Bunch(a="aaa", b="bbb"),
                profile0=Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )

        def tearDown(self):
            cleanup_workdir(self.workdir)

        def test__load(self):
            parser = PA.JsonConfigPaser("testapp")
            config = parser.load(self.paths[0])

            #pprint.pprint(config)
            for k, v in config.defaults.iteritems():
                self.assertEquals(self.config.defaults[k], v)

            for k, v in config.profile0.iteritems():
                self.assertEquals(self.config.profile0[k], v)

            self.assertEquals(self.config.array0, config.array0)


if PA.yaml is not None: 

    class TestYamlConfigParser(unittest.TestCase):

        def setUp(self):
            self.workdir = setup_workdir()

            conf = """\
defaults:
    a: aaa
    b: bbb

profile0:
    a: xxx
    b: yyy

array0: [1, 2, 3]
"""
            path = os.path.join(self.workdir, "config.yml")
            open(path, "w").write(conf)

            self.paths = [path]
            self.config = Bunch(
                defaults=Bunch(a="aaa", b="bbb"),
                profile0=Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )

        def tearDown(self):
            cleanup_workdir(self.workdir)

        def test__load(self):
            parser = PA.YamlConfigPaser("testapp")
            config = parser.load(self.paths[0])

            for k, v in config.defaults.iteritems():
                self.assertEquals(self.config.defaults[k], v)

            for k, v in config.profile0.iteritems():
                self.assertEquals(self.config.profile0[k], v)

            self.assertEquals(self.config.array0, config.array0)


# vim:sw=4 ts=4 et:
