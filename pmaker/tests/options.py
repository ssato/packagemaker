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
from pmaker.options import *
from pmaker.models.Bunch import Bunch
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.configurations as C
import pmaker.parser as P
import pmaker.environ as E

import optparse
import os
import os.path
import random
import tempfile
import unittest


class Test_00_setup_relations_option(unittest.TestCase):

    def test_01_setup_relations_option(self):
        p = optparse.OptionParser()
        p.add_option("", "--relations", **setup_relations_option())

        options, args = p.parse_args([])
        self.assertEquals(options.relations, [])

        return

        # TBD:
        relations_s = "obsoletes:mydata"
        options, args = p.parse_args(
            ["--relations", relations_s]
        )
        self.assertEquals(options.relations[0], ('obsoletes', ['mydata']))

        relations_s = "obsoletes:mydata;conflicts:mydata-old"
        options, args = p.parse_args(
            ["--relations", relations_s]
        )
        expected = P.parse(relations_s)
        self.assertEquals(options.relations, expected)

        self.assertEquals(options.relations[0], ('obsoletes', ['mydata']))
        self.assertEquals(options.relations[1], ('conflicts', ['mydata-old']))


class Test_01__set_workdir(unittest.TestCase):

    def test_00_set_workdir__no_changes(self):
        name, version = ("foo", "0.0.1")
        workdir = "/tmp/w/%s-%s" % (name, version)

        self.assertEquals(workdir, set_workdir(workdir, name, version))

    def test_01_set_workdir__absolute_workdir(self):
        workdir, name, version = ("/tmp/w", "foo", "0.0.1")
        self.assertEquals(
            "/tmp/w/foo-0.0.1",
            set_workdir(workdir, name, version)
        )

    def test_02_set_workdir__relative_workdir(self):
        workdir, name, version = ("../w", "foo", "0.0.1")
        abs_workdir = os.path.abspath(workdir)
        self.assertEquals(
            abs_workdir + "/foo-0.0.1",
            set_workdir(workdir, name, version)
        )


class Test_02_Options(unittest.TestCase):

    def test_00__init__(self):
        o = Options()

        # pmaker.options.Options is not resolvable because it would be hide
        # (decorated) with pmaker.utils.singleton() if it's decorated with
        # singleton() (@singleton). Here we use Bunch (parent class of Options
        # class) instead in such cases:
        # self.assertTrue(isinstance(o, Bunch))
        ## pmaker.options.Options is now not singleton:
        self.assertTrue(isinstance(o, Options))

        dfs = o.get_defaults()

        for k, v in C._defaults(E.Env()).iteritems():
            self.assertEquals(dfs[k], v)

    def test_01_parse_args_w_name_and_filelist(self):
        name = "foo"

        o = Options()
        pversion = o.config.pversion
        workdir = o.config.workdir

        (opts, args) = o.parse_args(["-n", name, "dummy_filelist.txt"])

        for k, v in o.get_defaults().iteritems():
            if k not in ("name", "summary", "workdir"):
                self.assertEquals(getattr(opts, k), v)
            else:
                v2 = getattr(opts, k)

                if k == "name":
                    self.assertEquals(v2, name)

                elif k == "workdir":
                    eworkdir = os.path.join(
                        workdir, "%s-%s" % (name, pversion)
                    )
                    self.assertEquals(v2, eworkdir)
                else:
                    self.assertEquals(v2, o.make_default_summary(name))

    def test_02_parse_args_w_name_and_filelist_and_verbose(self):
        name = "foo"

        o = Options()
        (opts, args) = o.parse_args(["-n", name, "-v", "dummy_filelist.txt"])

        self.assertEquals(opts.name, name)
        self.assertEquals(opts.verbosity, 1)

        (opts, args) = o.parse_args(["-n", name, "-vv", "dummy_filelist.txt"])
        self.assertEquals(opts.verbosity, 2)

        (opts, args) = o.parse_args(
            ["-n", name, "--debug", "dummy_filelist.txt"]
        )
        self.assertEquals(opts.verbosity, 2)

    def test_03_parse_args_w_name_and_filelist_and_template_path(self):
        name = "foo"
        cwd = os.path.join(os.getcwd(), "templates")
        paths_ref = E.Env().template_paths + [cwd]

        o = Options()
        (opts, args) = o.parse_args(
            ["-n", name, "--template-path", cwd, "dummy_filelist.txt"]
        )
        self.assertEquals(opts.template_paths, paths_ref)

    def test_04_parse_args_w_name_and_filelist_and_input_type(self):
        name = "foo"
        input_type = "filelist.json"

        o = Options()
        (opts, args) = o.parse_args(
            ["-n", name, "--input-type", input_type, "dummy_filelist.txt"]
        )
        self.assertEquals(opts.input_type, input_type)

    def test_05_parse_args_w_name_and_filelist_and_driver(self):
        name = "foo"
        driver = random.choice(
            [b for b in Backends.map().keys() if b != Backends.default()]
        )

        o = Options()
        (opts, args) = o.parse_args(
            ["-n", name, "--driver", driver, "dummy_filelist.txt"]
        )
        self.assertEquals(opts.driver, driver)

    def test_06_parse_args_w_name_and_filelist_and_compressor(self):
        name = "foo"
        env = E.Env()
        compressor = random.choice(
            [
                ct.extension for ct in env.compressors \
                    if ct.extension != env.compressor.extension
            ]
        )

        o = Options()
        (opts, args) = o.parse_args(
            ["-n", name, "--compressor", compressor, "dummy_filelist.txt"]
        )
        self.assertEquals(opts.compressor, compressor)

    def test_07_parse_args_w_name_and_filelist_and_no_mock(self):
        name = "foo"

        o = Options()
        (opts, args) = o.parse_args(
            ["-n", name, "--no-mock", "dummy_filelist.txt"]
        )
        self.assertTrue(opts.no_mock)

    def test_08_parse_args_w_name_and_filelist_and_relations(self):
        name = "foo"

        o = Options()
        (opts, args) = o.parse_args(
            ["-n", name, "--relations", "requires:/bin/sh",
                "dummy_filelist.txt"]
        )
        self.assertEquals(opts.relations[0], ('requires', ['/bin/sh']))

        (opts, args) = o.parse_args(
            ["-n", name,
             "--relations", "obsoletes:mydata;conflicts:mydata-old",
             "dummy_filelist.txt"
            ]
        )
        self.assertEquals(opts.relations[0], ('obsoletes', ['mydata']))
        self.assertEquals(opts.relations[1], ('conflicts', ['mydata-old']))


class Test_02_Options_w_side_effects(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_01_parse_args_w_name_and_changelog_option(self):
        name = "foo"
        changelog_file = os.path.join(self.workdir, "dummy_changelog.txt")
        changelog_content = "This is a dummy changelog file."

        o = Options()
        (opts, args) = o.parse_args(["-n", name, "dummy_filelist.txt"])
        self.assertEquals(opts.changelog, "")

        with open(changelog_file, "w") as f:
            f.write(changelog_content)

        o = Options()
        (opts, args) = o.parse_args(
            ["-n", name, "--changelog", changelog_file, "dummy_filelist.txt"]
        )
        self.assertEquals(opts.changelog, changelog_content)


# vim:sw=4 ts=4 et:
