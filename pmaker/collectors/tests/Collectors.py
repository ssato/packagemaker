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
from pmaker.collectors.Collectors import *
from pmaker.models.FileInfo import FileInfo
from pmaker.utils import dicts_comp
from pmaker.tests.common import setup_workdir, cleanup_workdir

import json
import optparse
import os.path
import unittest



class Test_00_FilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_00__parse(self):
        p0 = ""
        p1 = "#xxxxx"
        p2 = os.path.join(self.workdir, "a")
        p3 = os.path.join(self.workdir, "aa")
        p4 = os.path.join(self.workdir, "a*")

        for p in (p2, p3):
            os.system("touch " + p)

        ps2 = [FileInfo(p) for p in [p2]]
        ps3 = [FileInfo(p) for p in (p2, p3)]

        self.assertListEqual(FilelistCollector._parse(p0 + "\n"), [])
        self.assertListEqual(FilelistCollector._parse(p1 + "\n"), [])
        self.assertListEqual(FilelistCollector._parse(p2 + "\n"), ps2)
        self.assertListEqual(sorted(FilelistCollector._parse(p4 + "\n")), sorted(ps3))

    def test_01_list_fileinfos(self):
        paths = [
            "/etc/auto.*",
            "#/etc/aliases.db",
            "/etc/httpd/conf.d",
            "/etc/httpd/conf.d/*",
            "/etc/modprobe.d/*",
            "/etc/rc.d/init.d",
            "/etc/rc.d/rc",
            "/etc/reslv.conf",
        ]
        listfile = os.path.join(self.workdir, "files.list")

        open(listfile, "w").write("\n".join(p for p in paths))

        option_values = {
            "name": "foo",
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)

        fis = unique(concat(FilelistCollector._parse(p + "\n") for p in paths))
        self.assertListEqual(fis, fc.list_fileinfos(listfile))

    def test_02_collect(self):
        paths = [
            "/etc/at.deny",
            "/etc/auto.*",
            "#/etc/aliases.db",
            "/etc/httpd/conf.d",
            "/etc/httpd/conf.d/*",
            "/etc/modprobe.d/*",
            "/etc/rc.d/init.d",
            "/etc/rc.d/rc",
            "/etc/resolv.conf",
            "/etc/reslv.conf",  # should not be exist.
            "/etc/securetty",  # should not be exist.
        ]
        listfile = os.path.join(self.workdir, "files.list")

        open(listfile, "w").write("\n".join(p for p in paths))
        #f = open(listfile, "w")
        #for p in paths:
        #    f.write("%s\n" % p)
        #f.close()

        option_values = {
            "name": "foo",
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fs = fc.collect()

        option_values["format"] = "deb"
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fs = fc.collect()
        option_values["format"] = "rpm"

        option_values["destdir"] = "/etc"
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fs = fc.collect()
        option_values["destdir"] = ""

        option_values["ignore_owner"] = True
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fs = fc.collect()
        option_values["ignore_owner"] = False

        option_values["no_rpmdb"] = True
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fs = fc.collect()
        option_values["no_rpmdb"] = False

    def test_03_parse_line__ext(self):
        line = "/etc/resolv.conf,install_path=/var/lib/network/resolv.conf,uid=0,rpmattr='%config',create=1,content='nameserver 192.168.151.1\\n'"

        (paths, attrs) = FilelistCollector.parse_line(line)

        self.assertEquals(paths, ["/etc/resolv.conf"])
        self.assertEquals(attrs["install_path"], "/var/lib/network/resolv.conf")
        self.assertEquals(attrs["uid"], 0)
        self.assertEquals(attrs["rpmattr"], "%config")
        self.assertEquals(attrs["create"], 1)
        self.assertEquals(attrs["content"], "nameserver 192.168.151.1\\n")

    def test_04_collect__ext(self):
        paths = [
            "/etc/resolv.conf",
            "/etc/auto.*,uid=0,gid=0",
            "#/etc/aliases.db",
            "/etc/rc.d/rc,target=/etc/init.d/rc,uid=0,gid=0",
            "/etc/rc.d/rc.local,rpmattr=%config(noreplace)",
        ]
        listfile = os.path.join(self.workdir, "files.list")

        f = open(listfile, "w")
        for p in paths:
            f.write("%s\n" % p)
        f.close()

        option_values = {
            "name": "foo",
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, options)
        fs = fc.collect()



class Test_02_JsonFilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = setup_workdir()

        self.json_data = """\
{
    "files": [
        {
            "path": "/etc/resolv.conf",
            "attrs": {
                "target": "/var/lib/network/resolv.conf",
                "uid": 0,
                "gid": 0,
                "conflicts": "NetworkManager"
            }
        },
        {
            "path": "/etc/hosts",
            "attrs": {
                "conflicts": "setup",
                "rpmattr": "%config(noreplace)"
            }
        },
        {
            "path": "/etc/sysctl.conf"
        }
    ]
}
"""
        listfile = os.path.join(self.workdir, "files.json")

        f = open(listfile, "w")
        f.write(self.json_data)
        f.close()

        self.listfile = listfile

        option_values = {
            "name": "foo",
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        self.fc = JsonFilelistCollector(self.listfile, options)

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_01_list_fileinfos(self):
        ts = self.fc.list_fileinfos(self.listfile)

        self.assertFalse(len(ts) == 0)


# vim: set sw=4 ts=4 expandtab:
