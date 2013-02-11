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
import pmaker.configurations as C
import pmaker.environ as E
import pmaker.tests.common as T

import bunch as B
import os
import os.path
import unittest


class Test_01_functions(unittest.TestCase):

    def test_00__defaults(self):
        dfs = C._defaults(E.Env())

        self.assertTrue(isinstance(dfs, B.Bunch))

    def test_01__defaults_w_modified_env(self):
        dfs_ref = C._defaults(E.Env())

        env = E.Env()
        env.workdir = "/a/b/c"  # modified.

        dfs = C._defaults(E.Env())

        self.assertNotEquals(dfs_ref, dfs)
        self.assertEquals(dfs.workdir, env.workdir)


class Test_02_Config(unittest.TestCase):

    def setUp(self):
        self.workdir = T.setup_workdir()

    def tearDown(self):
        T.cleanup_workdir(self.workdir)

    def test_00__init__w_norc(self):
        cfg = C.Config(norc=True)
        dfs = C._defaults(E.Env())  # reference of cfg.

        for k, v in dfs.iteritems():
            self.assertEquals(getattr(cfg, k), v)

        self.assertTrue(cfg.missing_files())

    def test_01__norc_and_load_json_config(self):
        if E.json is None:
            return True

        cfg = C.Config(norc=True)
        dfs = C._defaults(E.Env())
        config = os.path.join(self.workdir, "test_config.json")

        content = """
{
    "verbosity": 1,
    "input_type": "filelist.json",
    "summary": "JSON Configuration test",
    "ignore_owner": true,
    "no_mock": true,
    "files": [
        {
            "path": "/a/b/c",
            "attrs" : {
                "create": true,
                "install_path": "/a/c",
                "uid": 100,
                "gid": 0,
                "rpmattr": "%config(noreplace)"
            }
        }
    ]
}
"""
        open(config, "w").write(content)
        cfg.load(config)

        self.assertEquals(cfg.verbosity, 1)
        self.assertEquals(cfg.input_type, "filelist.json")
        self.assertEquals(cfg.summary, "JSON Configuration test")
        self.assertEquals(cfg.ignore_owner, True)
        self.assertEquals(cfg.no_mock, True)

        self.assertNotEquals(cfg.files, None)
        self.assertFalse(cfg.missing_files())

    def test_02__norc_and_load_yaml_config(self):
        if E.yaml is None:
            return True

        cfg = C.Config(norc=True)
        dfs = C._defaults(E.Env())
        config = os.path.join(self.workdir, "test_config.yaml")

        content = """
verbosity: 1
input_type: filelist.yaml
summary: YAML Configuration test
ignore_owner: true
no_mock: true
files:
    - path: /a/b/c
      attrs:
        create: true
        install_path: /a/c
        uid: 100
        gid: 0
        rpmattr: "%config(noreplace)"
"""
        open(config, "w").write(content)
        cfg.load(config)

        self.assertEquals(cfg.verbosity, 1)
        self.assertEquals(cfg.input_type, "filelist.yaml")
        self.assertEquals(cfg.summary, "YAML Configuration test")
        self.assertEquals(cfg.ignore_owner, True)
        self.assertEquals(cfg.no_mock, True)

        self.assertNotEquals(cfg.files, None)
        self.assertFalse(cfg.missing_files())


# vim:sw=4:ts=4:et:
