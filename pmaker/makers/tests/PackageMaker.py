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
from pmaker.makers.PackageMaker import *
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.collectors.Filters import *
from pmaker.config import Config
from pmaker.package import Package

import logging
import optparse
import os
import os.path
import random
import sys
import tempfile
import unittest



class Test_00_to_srcdir(unittest.TestCase):

    def test_to_srcdir(self):
        srcdir = "/tmp/w/src"

        self.assertEquals(to_srcdir(srcdir, "/a/b/c"), "/tmp/w/src/a/b/c")
        self.assertEquals(to_srcdir(srcdir, "a/b"),    "/tmp/w/src/a/b")
        self.assertEquals(to_srcdir(srcdir, "/"),      "/tmp/w/src/")



class Test_01_PackageMaker__generated_files(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

        targets = [os.path.join(self.workdir, p) for p in ("aaa.txt", "bbb.txt", "c/d/e.txt")]
        os.makedirs(os.path.join(self.workdir, "c/d/"))
        for t in targets:
            os.system("touch " + t)
        self.targets = targets

        self.fileinfos = [FileInfoFactory().create(f) for f in targets]

        defaults = Config.defaults()
        defaults["workdir"] = self.workdir
        defaults["name"] = "foo"

        self.options = optparse.Values(defaults)
        self.package = Package(self.options)

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def helper_run_upto_step(self, step):
        pmaker = PackageMaker(self.package, self.fileinfos, self.options)
        pmaker.upto = step

        try:
            pmaker.run()
        except SystemExit:
            pass

        self.assertTrue(os.path.exists(pmaker.touch_file(step)))

    def test_00_shell(self):
        pmaker = PackageMaker(self.package, self.fileinfos, self.options)

        self.assertEquals(pmaker.shell("true"), 0)

    def test_01_genfile(self):
        pmaker = PackageMaker(self.package, self.fileinfos, self.options)

        templatedir = os.path.join(self.workdir, "templates")
        os.makedirs(templatedir)

        tmpl = os.path.join(templatedir, "aaa")
        open(tmpl, "w").write("$name")
        outfile = "out.txt"

        pmaker.template_paths = [templatedir]

        pmaker.genfile("aaa", outfile)

        self.assertTrue(os.path.exists(os.path.join(self.workdir, outfile)))
        self.assertEquals(open(os.path.join(self.workdir, outfile)).read(), self.package.name)

    def test_02_copyfiles(self):
        pmaker = PackageMaker(self.package, self.fileinfos, self.options)
        pmaker.copyfiles()

        for t in self.targets:
            p = os.path.join(pmaker.srcdir, t[1:])
            self.assertTrue(os.path.exists(p))

    def test_03_save__and__load(self):
        pmaker = PackageMaker(self.package, self.fileinfos, self.options)
        pmaker.save()
        pmaker.load()

    def test_04_run__setup(self):
        self.helper_run_upto_step(STEP_SETUP)

    def test_05_run__preconfigure(self):
        self.helper_run_upto_step(STEP_PRECONFIGURE)

    def test_06_run__configure(self):
        self.helper_run_upto_step(STEP_CONFIGURE)

    def test_07_run__sbuild(self):
        self.helper_run_upto_step(STEP_SBUILD)

    def test_08_run__build(self):
        self.helper_run_upto_step(STEP_BUILD)



class Test_02_PackageMaker__system_files(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

        paths = [
            "/etc/aliases.db",
            "/etc/at.deny",
            "/etc/auto.master",
            "/etc/hosts",
            "/etc/httpd/conf/httpd.conf",
            "/etc/modprobe.d/blacklist.conf",
            "/etc/rc.d/init.d",
            "/etc/rc.d/rc",
            "/etc/resolv.conf",
            "/etc/secure.tty",
            "/etc/security/access.conf",
            "/etc/security/limits.conf",
            "/etc/shadow",
            "/etc/skel",
            "/etc/system-release",
            "/etc/sudoers",
        ]

        paths = random.sample([p for p in paths if os.path.exists(p)], 10)

        filters = [UnsupportedTypesFilter(), ReadAccessFilter()]
        fileinfos = [FileInfoFactory().create(p) for p in paths]
        fileinfos = [fi for fi in fileinfos if not any(f.pred(fi) for f in filters)]

        defaults = Config.defaults()
        defaults["workdir"] = self.workdir
        defaults["name"] = "foo"

        options = optparse.Values(defaults)
        package = Package(options)

        self.pmaker = AutotoolsTgzPackageMaker(package, fileinfos, options)
        self.pmaker.template_paths = [os.path.join(os.getcwd(), "templates")]

        logging.getLogger().setLevel(logging.WARNING) # suppress log messages

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def helper_run_upto_step(self, step):
        self.pmaker.upto = step

        try:
            self.pmaker.run()
        except SystemExit:
            pass

        self.assertTrue(os.path.exists(self.pmaker.touch_file(step)))

    def test_01_preconfigure(self):
        self.helper_run_upto_step(STEP_PRECONFIGURE)

    def test_02_configure(self):
        self.helper_run_upto_step(STEP_CONFIGURE)

    def test_03_sbuild(self):
        self.helper_run_upto_step(STEP_SBUILD)

    def test_04_build(self):
        self.helper_run_upto_step(STEP_BUILD)



class Test_03_AutotoolsTgzPackageMaker__single(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        target_path = os.path.join(self.workdir, "a.txt")

        open(target_path, "w").write("a\n")

        fileinfos = [FileInfoFactory().create(target_path)]

        defaults = Config.defaults()
        defaults["workdir"] = self.workdir
        defaults["name"] = "foo"

        options = optparse.Values(defaults)
        package = Package(options)

        self.pmaker = AutotoolsTgzPackageMaker(package, fileinfos, options)
        self.pmaker.template_paths = [os.path.join(os.getcwd(), "templates")]

        logging.getLogger().setLevel(logging.WARNING) # suppress log messages

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def helper_run_upto_step(self, step):
        self.pmaker.upto = step

        try:
            self.pmaker.run()
        except SystemExit:
            pass

        self.assertTrue(os.path.exists(self.pmaker.touch_file(step)))

    def test_01_preconfigure(self):
        self.helper_run_upto_step(STEP_PRECONFIGURE)

    def test_02_configure(self):
        self.helper_run_upto_step(STEP_CONFIGURE)

    def test_03_sbuild(self):
        self.helper_run_upto_step(STEP_SBUILD)

    def test_04_build(self):
        self.helper_run_upto_step(STEP_BUILD)


# vim: set sw=4 ts=4 expandtab:
