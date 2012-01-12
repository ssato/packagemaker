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
import pmaker.anycfg as A
import pmaker.models.Bunch as B
import pmaker.tests.common as C

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

        paths_r = A.list_paths(prog, None)

        for p in paths:
            self.assertTrue(p in paths_r,
                "Expected %s in %s" % (p, str(paths_r)))

    def test_list_paths__not_None(self):
        self.assertEquals(["/a/b/c"], A.list_paths("testapp", ["/a/b/c"]))


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
        self.workdir = C.setup_workdir()
        path = dump_conf(self.workdir, INI_CONFIG_CONTENT)
        self.paths = [path]
        self.config = B.Bunch(
            a="aaa",
            b="bbb",
            profile0=B.Bunch(a="xxx", b="yyy", c=[1, 2, 3]),
        )

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test__load(self):
        parser = A.IniConfigParser()
        config = parser.load(self.paths[0])

        self.assertEquals(config, self.config)


class Test_02_IniConfigParser(unittest.TestCase):

    def test_00_load(self):
        cfgpath = os.path.join(C.selfdir(), "config_example_00.ini")

        parser = A.IniConfigParser()
        config = parser.load(cfgpath)

    def test_01_load(self):
        cfgpath = os.path.join(C.selfdir(), "config_example_01.ini")

        parser = A.IniConfigParser()
        config = parser.load(cfgpath)


if A.json is not None:

    class Test_03_JsonConfigParser(unittest.TestCase):

        def setUp(self):
            self.workdir = C.setup_workdir()
            path = dump_conf(self.workdir, JSON_CONFIG_CONTENT, ".json")
            self.paths = [path]
            self.config = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )

        def tearDown(self):
            C.cleanup_workdir(self.workdir)

        def test_00_load(self):
            parser = A.JsonConfigPaser()
            config = parser.load(self.paths[0])

            self.assertEquals(config, self.config)

        def test_01_dump(self):
            conf2 = os.path.join(self.workdir, "dumped_config.json")
            A.JsonConfigPaser.dump(self.config, conf2)

            self.assertTrue(os.path.exists(conf2))

    class Test_04_JsonConfigParser(unittest.TestCase):

        def test_00_load(self):
            cfgpath = os.path.join(C.selfdir(), "config_example_00.json")

            parser = A.JsonConfigPaser()
            config = parser.load(cfgpath)

            self.assertEquals(config.config, None)
            self.assertEquals(config.norc, False)
            self.assertEquals(config.force, False)
            self.assertEquals(config.verbosity, 0)
            self.assertEquals(config.name, "example-00-app")
            self.assertEquals(config.group, "System Environment/Base")
            self.assertEquals(config.license, "GPLv3+")
            self.assertEquals(config.url, "http://example.com")
            self.assertEquals(config.summary, "Example 00 app")
            self.assertEquals(config.arch, False)
            self.assertEquals(config.relations, "requires:/bin/sh")
            self.assertEquals(config.pversion, "0.0.1")
            self.assertEquals(config.release, 1)
            self.assertEquals(config.no_mock, True)

            self.assertNotEquals(config.files, [])
            self.assertEquals(config.files[0].path, "/a/b/c")
            self.assertEquals(config.files[0].attrs.create, 0)
            self.assertEquals(config.files[1].path, "/d/e")

        def test_01_load(self):
            cfgpath = os.path.join(C.selfdir(), "config_example_01.json")

            parser = A.JsonConfigPaser()
            config = parser.load(cfgpath)


if A.yaml is not None:

    class Test_05_YamlConfigParser(unittest.TestCase):

        def setUp(self):
            self.workdir = C.setup_workdir()
            path = dump_conf(self.workdir, YAML_CONFIG_CONTENT, ".yml")
            self.paths = [path]
            self.config = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )

        def tearDown(self):
            C.cleanup_workdir(self.workdir)

        def test_00_load(self):
            parser = A.YamlConfigPaser()
            config = parser.load(self.paths[0])

            self.assertEquals(config, self.config)

        def test_01_dump(self):
            conf2 = os.path.join(self.workdir, "dumped_config.yaml")
            A.YamlConfigPaser.dump(self.config, conf2)

            self.assertTrue(os.path.exists(conf2))

    class Test_06_YamlConfigParser(unittest.TestCase):

        def test_00_load(self):
            cfgpath = os.path.join(C.selfdir(), "config_example_00.yaml")

            parser = A.YamlConfigPaser()
            config = parser.load(cfgpath)

            self.assertEquals(config.config, None)
            self.assertEquals(config.norc, False)
            self.assertEquals(config.force, False)
            self.assertEquals(config.verbosity, 0)
            self.assertEquals(config.name, "example-00-app")
            self.assertEquals(config.group, "System Environment/Base")
            self.assertEquals(config.license, "GPLv3+")
            self.assertEquals(config.url, "http://example.com")
            self.assertEquals(config.summary, "Example 00 app")
            self.assertEquals(config.arch, False)
            self.assertEquals(config.relations, "requires:/bin/sh")
            self.assertEquals(config.pversion, "0.0.1")
            self.assertEquals(config.release, 1)
            self.assertEquals(config.no_mock, True)

            self.assertNotEquals(config.files, [])
            self.assertEquals(config.files[0].path, "/a/b/c")
            self.assertEquals(config.files[0].attrs.create, 0)
            self.assertEquals(config.files[1].path, "/d/e")


class Test_07_AnyConfigParser(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_01_load(self):
        parser = A.AnyConfigParser()

        path = dump_conf(self.workdir, INI_CONFIG_CONTENT)
        config_ref = B.Bunch(
            a="aaa",
            b="bbb",
            profile0=B.Bunch(a="xxx", b="yyy", c=[1, 2, 3]),
        )
        config = parser.load(path)
        self.assertEquals(config, config_ref)

        if A.json:
            path = dump_conf(self.workdir, JSON_CONFIG_CONTENT, ".json")
            config_ref = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path)
            self.assertEquals(config, config_ref)

        if A.yaml:
            path = dump_conf(self.workdir, YAML_CONFIG_CONTENT, ".yaml")
            config_ref = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path)
            self.assertEquals(config, config_ref)

    def test_02_loads(self):
        parser = A.AnyConfigParser()

        path = dump_conf(self.workdir, INI_CONFIG_CONTENT)
        config_ref = B.Bunch(
            a="aaa",
            b="bbb",
            profile0=B.Bunch(a="xxx", b="yyy", c=[1, 2, 3]),
        )
        paths = [path]

        if A.json:
            content = '{"array0": [1, 2, 3]}'
            path = dump_conf(self.workdir, content, ".json")
            config_ref["array0"] = [1, 2, 3]
            paths.append(path)

        if A.yaml:
            content = """\
profile0:
    b: zzz
"""
            path = dump_conf(self.workdir, content, ".yaml")
            config_ref.profile0.b = "zzz"
            paths.append(path)

        config = parser.loads("dummy_name", paths)

        self.assertEquals(config, config_ref)

    def test_03_load__init__w_type__json(self):
        parser = A.AnyConfigParser(A.CTYPE_JSON)

        if A.json:
            path = dump_conf(self.workdir, JSON_CONFIG_CONTENT, ".conf")
            config_ref = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path)
            self.assertEquals(config, config_ref)

    def test_04_load__init__w_type__yaml(self):
        parser = A.AnyConfigParser(A.CTYPE_YAML)

        if A.yaml:
            path = dump_conf(self.workdir, YAML_CONFIG_CONTENT, ".conf")
            config_ref = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path)
            self.assertEquals(config, config_ref)

    def test_05_load__w_type_json(self):
        parser = A.AnyConfigParser()

        if A.json:
            path = dump_conf(self.workdir, JSON_CONFIG_CONTENT, ".conf")
            config_ref = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path, A.CTYPE_JSON)
            self.assertEquals(config, config_ref)

    def test_06_load__w_type_yaml(self):
        parser = A.AnyConfigParser()

        if A.yaml:
            path = dump_conf(self.workdir, YAML_CONFIG_CONTENT, ".conf")
            config_ref = B.Bunch(
                defaults=B.Bunch(a="aaa", b="bbb"),
                profile0=B.Bunch(a="xxx", b="yyy"),
                array0=[1, 2, 3],
            )
            config = parser.load(path, A.CTYPE_YAML)
            self.assertEquals(config, config_ref)

    def test_07_dump__json(self):
        conf0 = os.path.join(C.selfdir(), "config_example_01.json")
        conf1 = os.path.join(self.workdir, "dumped_config_example_01.json")

        parser = A.AnyConfigParser()
        data = parser.load(conf0)

        A.AnyConfigParser.dump(data, conf1)
        self.assertTrue(os.path.exists(conf1))

    def test_08_dump__yaml(self):
        conf0 = os.path.join(C.selfdir(), "config_example_01.yaml")
        conf1 = os.path.join(
            self.workdir, "dumped_config_example_01.yaml"
        )

        parser = A.AnyConfigParser()
        data = parser.load(conf0)

        A.AnyConfigParser.dump(data, conf1)
        self.assertTrue(os.path.exists(conf1))


# vim:sw=4 ts=4 et:
