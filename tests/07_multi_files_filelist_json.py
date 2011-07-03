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
from pmaker.utils import rm_rf
from pmaker.globals import *
from tests.utils import *

import logging
import os
import os.path
import unittest


if JSON_ENABLED:
    import json



JSON_FILELIST_0 = """
{
    "files": [
        {
            "path": "aaa.txt"
        },
        {
            "path": "bbb.txt",
            "target": {
                "uid": 100,
                "gid": 0
            }
        },
        {
            "path": "c/d/e/f.txt",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        }
    ]
}
"""


JSON_FILELIST_1 = """
{
    "files": [
        {
            "path": "/etc/aliases.db",
            "target": {
                "uid": 10,
                "gid": 10
            }
        },
        {
            "path": "/etc/at.deny"
        },
        {
            "path": "/etc/auto.master"
        },
        {
            "path": "/etc/hosts",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/httpd/conf/httpd.conf",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/modprobe.d/blacklist.conf",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/rc.d/init.d"
        },
        {
            "path": "/etc/rc.d/rc",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/resolv.conf",
            "target": {
                "target": "/var/lib/networks.d/resolv.conf",
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/secure.tty",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/security/access.conf",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/security/limits.conf",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/shadow",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/skel"
        },
        {
            "path": "/etc/system-release",
            "target": {
                "rpmattr": "%config"
            }
        },
        {
            "path": "/etc/sudoers",
            "target": {
                "rpmattr": "%config(noreplace)"
            }
        }
    ]
}
"""


class Test_00_multi_files_filelist_json(unittest.TestCase):

    def setUp(self):
        self.workdir = helper_create_tmpdir()
        self.pmworkdir = os.path.join(self.workdir, "pm")
        self.listfile = os.path.join(self.workdir, "files.list")
        self.template_path = os.path.join(os.getcwd(), "templates")

    def tearDown(self):
        rm_rf(self.workdir)

    def prepare_json_filelist__generated_files(self):
        data = json.loads(JSON_FILELIST_0)
        data2 = dict(); data2["files"] = []

        for t in data["files"]:
            # rewrite path: path -> workdir/path
            path = t["path"]
            path = t["path"] = os.path.join(self.workdir, path)
            pdir = os.path.dirname(path)

            if not os.path.exists(pdir):
                os.makedirs(pdir)

            os.system("touch " + path)

            data2["files"].append(t)

        json.dump(data2, open(self.listfile, "w"))

    def prepare_json_filelist__system_files(self):
        data = json.loads(JSON_FILELIST_1)
        data2 = dict(); data2["files"] = []

        for t in data["files"]:
            if os.path.exists(t["path"]):
                data2["files"].append(t)

        json.dump(data2, open(self.listfile, "w"))

    def test_00_generated_files__tgz(self):
        if not JSON_ENABLED:
            return

        self.prepare_json_filelist__generated_files()

        args = "--name foobar --template-path %s -w %s --format %s --itype filelist.json %s" % \
            (self.template_path, self.pmworkdir, "tgz", self.listfile)
        helper_run_with_args(args)

    def test_01_system_files__tgz(self):
        if not JSON_ENABLED:
            return

        self.prepare_json_filelist__system_files()

        args = "--name foobar --template-path %s -w %s --format %s --itype filelist.json %s" % \
            (self.template_path, self.pmworkdir, "tgz", self.listfile)
        helper_run_with_args(args)

    def test_02_generated_files__rpm__no_mock(self):
        if not JSON_ENABLED:
            return

        if not helper_is_rpm_based_system():
            return

        self.prepare_json_filelist__generated_files()

        args = "--name foobar --template-path %s -w %s --format %s --itype filelist.json %s --no-mock" % \
            (self.template_path, self.pmworkdir, "rpm", self.listfile)
        helper_run_with_args(args)

    def test_03_system_files__rpm__no_mock(self):
        if not JSON_ENABLED:
            return

        if not helper_is_rpm_based_system():
            return

        self.prepare_json_filelist__system_files()

        args = "--name foobar --template-path %s -w %s --format %s --itype filelist.json %s --no-mock" % \
            (self.template_path, self.pmworkdir, "rpm", self.listfile)
        helper_run_with_args(args)


# vim: set sw=4 ts=4 expandtab:
