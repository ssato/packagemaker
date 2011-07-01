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

import optparse
import os.path
import tempfile
import unittest



class TestFilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test__parse(self):
        p0 = ""
        p1 = "#xxxxx"
        p2 = os.path.join(self.workdir, "a")
        p3 = os.path.join(self.workdir, "aa")
        p4 = os.path.join(self.workdir, "a*")

        for p in (p2, p3):
            os.system("touch " + p)

        ps2 = [Target(p) for p in [p2]]
        ps3 = [Target(p) for p in [p2, p3]]

        self.assertListEqual(FilelistCollector._parse(p0 + "\n"), [])
        self.assertListEqual(FilelistCollector._parse(p1 + "\n"), [])
        self.assertListEqual(FilelistCollector._parse(p2 + "\n"), ps2)
        self.assertListEqual(sorted(FilelistCollector._parse(p4 + "\n")), sorted(ps3))

    def test_list_targets(self):
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

        f = open(listfile, "w")
        f.write("\n")
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

        ts = unique(concat(FilelistCollector._parse(p + "\n") for p in paths))
        self.assertListEqual(ts, fc.list_targets(listfile))

    def test_collect(self):
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



class TestExtFilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test_collect(self):
        paths = [
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
        fc = ExtFilelistCollector(listfile, options)
        fs = fc.collect()



class TestJsonFilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        self.json_data = """\
[
    {
        "path": "/etc/resolv.conf",
        "target": {
            "target": "/var/lib/network/resolv.conf",
            "uid": 0,
            "gid": 0,
            "conflicts": "NetworkManager"
        }
    },
    {
        "path": "/etc/hosts",
        "target": {
            "conflicts": "setup",
            "rpmattr": "%config(noreplace)"
        }
    }
]
"""

    def tearDown(self):
        rm_rf(self.workdir)

    def test_list_targets(self):
        listfile = os.path.join(self.workdir, "files.json")

        f = open(listfile, "w")
        f.write(self.json_data)
        f.close()

        option_values = {
            "name": "foo",
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = ExtFilelistCollector(listfile, options)

        ts = fc.list_targets(listfile)
        #self.assertListEqual(ts, ts2)


# vim: set sw=4 ts=4 expandtab:
