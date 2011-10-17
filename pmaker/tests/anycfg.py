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


class Test_00__list_paths(unittest.TestCase):

    def test_list_paths__None(self):
        prog = "testapp"
        home = os.environ.get("HOME", os.curdir)

        paths = ["/etc/%s.conf" % prog]
        paths += sorted(glob.glob("/etc/%s.d/*.conf" % prog))
        paths += [os.path.join(home, ".config", prog)]
        paths += [
            os.environ.get(
                "%sRC" % prog.upper(),
                os.path.join(home, ".%src" % prog)
            )
        ]

        paths_r = PA.list_paths(prog, None)

        for p in paths:
            self.assertTrue(p in paths_r,
                "Expected %s in %s" % (p, str(paths_r)))

    def test_list_paths__not_None(self):
        self.assertEquals(["/a/b/c"], PA.list_paths("testapp", ["/a/b/c"]))


INI_CONFIG_CONTENT = """[DEFAULT]
a: aaa
b: bbb

[profile0]
a: xxx
b: yyy
c: 1,2,3
"""

JSON_CONFIG_CONTENT = """{
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

YAML_CONFIG_CONTENT = """defaults:
    a: aaa
    b: bbb

profile0:
    a: xxx
    b: yyy

array0: [1, 2, 3]
"""


def dump_conf(workdir, content, ext=""):
        path = os.path.join(workdir, "config" + ext)
        print >> open(path, "w"), content

        return path


class Test_01_IniConfigParser(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        path = dump_conf(self.workdir, INI_CONFIG_CONTENT)
        self.paths = [path]
        self.config = Bunch(
            defaults=Bunch(a="aaa", b="bbb"),
            profile0=Bunch(a="xxx", b="yyy", c=[1, 2, 3]),
        )

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test__load(self):
        parser = PA.IniConfigParser()
        config = parser.load(self.paths[0])

        self.assertEquals(config, self.config)


if PA.json is not None:

    class Test_02_JsonConfigParser(unittest.TestCase):

        def setUp(self):
            self.workdir = setup_workdir()
            path = dump_conf(self.workdir, JSON_CONFIG_CONTENT, ".json")
            self.paths = [path]
            self.config = Bunch(
                defaults=Bunch(a="aaa", b="bbb"),
                profile0=Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )

        def tearDown(self):
            cleanup_workdir(self.workdir)

        def test__load(self):
            parser = PA.JsonConfigPaser()
            config = parser.load(self.paths[0])

            self.assertEquals(config, self.config)


if PA.yaml is not None:

    class Test_03_YamlConfigParser(unittest.TestCase):

        def setUp(self):
            self.workdir = setup_workdir()
            path = dump_conf(self.workdir, YAML_CONFIG_CONTENT, ".yml")
            self.paths = [path]
            self.config = Bunch(
                defaults=Bunch(a="aaa", b="bbb"),
                profile0=Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )

        def tearDown(self):
            cleanup_workdir(self.workdir)

        def test__load(self):
            parser = PA.YamlConfigPaser()
            config = parser.load(self.paths[0])

            self.assertEquals(config, self.config)


class Test_04_AnyConfigParser(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_01_load(self):
        parser = PA.AnyConfigParser()

        path = dump_conf(self.workdir, INI_CONFIG_CONTENT)
        config_ref = Bunch(
            defaults=Bunch(a="aaa", b="bbb"),
            profile0=Bunch(a="xxx", b="yyy", c=[1, 2, 3]),
        )
        config = parser.load(path)
        self.assertEquals(config, config_ref)

        if PA.json:
            path = dump_conf(self.workdir, JSON_CONFIG_CONTENT, ".json")
            config_ref = Bunch(
                defaults=Bunch(a="aaa", b="bbb"),
                profile0=Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path)
            self.assertEquals(config, config_ref)

        if PA.yaml:
            path = dump_conf(self.workdir, YAML_CONFIG_CONTENT, ".yaml")
            config_ref = Bunch(
                defaults=Bunch(a="aaa", b="bbb"),
                profile0=Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path)
            self.assertEquals(config, config_ref)

    def test_02_loads(self):
        parser = PA.AnyConfigParser()

        path = dump_conf(self.workdir, INI_CONFIG_CONTENT)
        config_ref = Bunch(
            defaults=Bunch(a="aaa", b="bbb"),
            profile0=Bunch(a="xxx", b="yyy", c=[1, 2, 3]),
        )
        paths = [path]

        if PA.json:
            content = '{"array0": [1, 2, 3]}'
            path = dump_conf(self.workdir, content, ".json")
            config_ref["array0"] = [1, 2, 3]
            paths.append(path)

        if PA.yaml:
            content = """\
profile0:
    b: zzz
"""
            path = dump_conf(self.workdir, content, ".yaml")
            config_ref.profile0.b = "zzz"
            paths.append(path)

        config = parser.loads("dummy_name", paths)

        self.assertEquals(config, config_ref)


# vim:sw=4 ts=4 et:
