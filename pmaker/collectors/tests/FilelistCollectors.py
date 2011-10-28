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
from pmaker.collectors.FilelistCollectors import FilelistCollector, \
    AnyFilelistCollector
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.anycfg as Anycfg
import pmaker.collectors.Filters as Filters
import pmaker.environ as E
import pmaker.models.FileObjectFactory as Factory
import pmaker.options as O
import pmaker.utils as U

import glob
import os
import os.path
import random
import unittest


PATHS = [
    "/etc/auto.*",  # glob; will be expanded to path list.
    "#/etc/aliases.db",  # comment; will be ignored.
    "/etc/httpd/conf.d",
    "/etc/httpd/conf.d/*",  # glob
    "/etc/modprobe.d/*",  # glob
    "/etc/rc.d/init.d",  # dir, not file
    "/etc/rc.d/rc",
    "/etc/resolv.conf",
    "/etc/reslv.conf",  # should not exist
    "/etc/grub.conf",  # should not be able to read
    "/usr/share/automake-*/am/*.am",  # glob
    "/var/run/*",  # glob, and some of them should not be able to read
    "/root/*",  # likewise.
]

PATHS_EXPANDED = U.unique(
    U.concat(
        "*" in p and glob.glob(p) or [p] for p in PATHS \
            if not p.startswith("#")
    )
)


def init_config(listfile):
    o = O.Options()
    (opts, args) = o.parse_args(["-n", "foo", listfile])
    return opts


class Test_00_FilelistCollector__wo_side_effects(unittest.TestCase):

    def test_00__init__(self):
        listfile = "/a/b/c/path.conf"  # dummy
        config = init_config(listfile)

        collector = FilelistCollector(listfile, config)

        self.assertTrue(isinstance(collector, FilelistCollector))
        self.assertEquals(collector.listfile, listfile)

    def test_01__parse__none(self):
        listfile = "/a/b/c/path.conf"
        config = init_config(listfile)

        line = "# this is a comment line to be ignored\n"

        collector = FilelistCollector(listfile, config)
        fos = collector._parse(line)

        self.assertEquals(fos, [])

    def test_02__parse__single_virtual_file(self):
        listfile = "/a/b/c/path.conf"
        config = init_config(listfile)

        line = " %s,create=1,content=\"generated file\" \n" % listfile

        collector = FilelistCollector(listfile, config)
        fos = collector._parse(line)
        fos_ref = [
            Factory.create(listfile, False,
                create=1, content="generated file"
            ),
        ]

        self.assertNotEquals(fos, [])
        self.assertEquals(fos, fos_ref)


class Test_01_FilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test_01__parse__multi_real_file(self):
        listfile = os.path.join(self.workdir, "file.list")
        listfile2 = os.path.join(self.workdir, "file2.list")
        config = init_config(listfile)

        line = "%s/file*.list,mode=0644\n" % self.workdir
        open(listfile, "w").write(line)
        open(listfile2, "w").write(line)

        collector = FilelistCollector(listfile, config)
        fos = collector._parse(line)
        fos_ref = [
            Factory.create(listfile, False, mode="0644"),
            Factory.create(listfile2, False, mode="0644"),
        ]

        self.assertEquals(sorted(fos), sorted(fos_ref))

    def test_02_list__multi_generated_file(self):
        listfile = os.path.join(self.workdir, "file.list")
        listfile2 = os.path.join(self.workdir, "file2.list")
        config = init_config(listfile)

        line = "%s/file*.list,mode=0644\n" % self.workdir
        open(listfile, "w").write(line)
        open(listfile2, "w").write(line)

        collector = FilelistCollector(listfile, config)
        fos = collector.list(listfile)
        fos_ref = [
            Factory.create(listfile, False, mode="0644"),
            Factory.create(listfile2, False, mode="0644"),
        ]

        self.assertEquals(sorted(fos), sorted(fos_ref))

    def test_03_list__multi_real_files(self):
        listfile = os.path.join(self.workdir, "file.list")
        config = init_config(listfile)

        open(listfile, "w").write("\n".join(PATHS))

        collector = FilelistCollector(listfile, config)

        fos = collector.list(listfile)
        fos_ref = sorted(
            Factory.create(p, False) for p in PATHS_EXPANDED
        )

        self.assertEquals(sorted(fos), fos_ref)

    def test_04_collect__single_real_file(self):
        path = random.choice(
            ["/etc/hosts", "/etc/resolv.conf", "/etc/services"]
        )

        listfile = os.path.join(self.workdir, "file.list")
        config = init_config(listfile)

        open(listfile, "w").write(path + "\n")

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()
        fo_ref = Factory.create(path, False)

        self.assertEquals(fos[0].path, path)
        self.assertEquals(fos, [fo_ref])

    def test_05_collect__single_real_file__no_read_access(self):
        if os.getuid() == 0:
            print >> sys.stderr, "You look root and cannot test this. Skipped"
            return

        path = random.choice(
            ["/etc/shadow", "/etc/securetty", "/etc/gshadow"]
        )

        listfile = os.path.join(self.workdir, "file.list")
        config = init_config(listfile)

        open(listfile, "w").write(path + "\n")

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()

        self.assertEquals(fos, [])

    def test_06_collect__single_real_file__not_supported_type(self):
        path = random.choice(
            ["/dev/null", "/dev/zero", "/dev/random"]
        )

        listfile = os.path.join(self.workdir, "file.list")
        config = init_config(listfile)

        open(listfile, "w").write(path + "\n")

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()

        self.assertEquals(fos, [])

    def test_07_collect__single_real_file__destdir_mod(self):
        listfile = path = os.path.join(self.workdir, "file.list")

        config = init_config(listfile)
        config.destdir = self.workdir

        open(listfile, "w").write(path + "\n")

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()
        fo_ref = Factory.create(path, False)

        self.assertEquals(
            os.path.join(self.workdir, fos[0].path),
            fo_ref.path
        )

    def test_08_collect__single_real_file__ignore_owner_mod(self):
        listfile = path = os.path.join(self.workdir, "file.list")

        config = init_config(listfile)
        config.ignore_owner = True

        open(listfile, "w").write(path + "\n")

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()
        fo_ref = Factory.create(path, False)

        self.assertEquals(fos[0].uid, 0)
        self.assertEquals(fos[0].gid, 0)

    def test_09_collect__single_real_file__rpmattr(self):
        path = random.choice(["/etc/hosts", "/etc/services"])

        listfile = os.path.join(self.workdir, "file.list")
        config = init_config(listfile)
        config.driver = "autotools.single.rpm"

        open(listfile, "w").write(path + "\n")

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()
        fo_ref = Factory.create(path, False)

        self.assertEquals(fos, [fo_ref])
        self.assertTrue("rpm_attr" in fos[0])

    def test_10_collect__single_real_file__rpmconflicts(self):
        path = random.choice(
            ["/etc/hosts", "/etc/services", "/bin/sh"]
        )

        listfile = os.path.join(self.workdir, "file.list")
        config = init_config(listfile)
        config.driver = "autotools.single.rpm"
        config.no_rpmdb = False

        open(listfile, "w").write(path + "\n")

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()

        self.assertTrue("save_path" in fos[0])

    def test_15_collect__multi_real_files(self):
        listfile = os.path.join(self.workdir, "file.list")
        config = init_config(listfile)

        open(listfile, "w").write("\n".join(PATHS))

        collector = FilelistCollector(listfile, config)

        fos = collector.collect()

        filters = [
            Filters.UnsupportedTypesFilter(),
            Filters.NotExistFilter(),
            Filters.ReadAccessFilter(),
        ]
        fos_ref = sorted(
            Factory.create(p, False) for p in PATHS_EXPANDED
        )
        fos_ref = [
            f for f in fos_ref if not any(filter(f) for filter in filters)
        ]

        self.assertEquals(sorted(fos), fos_ref)


class Test_02_AnyFilelistCollector__wo_side_effects(unittest.TestCase):

    def test_01__init__wo_itype(self):
        listfile = "dummy.list"
        config = init_config(listfile)
        ac = AnyFilelistCollector(listfile, config)

        self.assertTrue(isinstance(ac, AnyFilelistCollector))

    def test_02__init__w_itype(self):
        listfile = "dummy.list"
        config = init_config(listfile)

        ac = AnyFilelistCollector(listfile, config, Anycfg.CTYPE_JSON)
        self.assertTrue(isinstance(ac, AnyFilelistCollector))
        self.assertTrue(ac.itype, Anycfg.CTYPE_JSON)

        ac = AnyFilelistCollector(listfile, config, Anycfg.CTYPE_YAML)
        self.assertTrue(isinstance(ac, AnyFilelistCollector))
        self.assertTrue(ac.itype, Anycfg.CTYPE_YAML)


class Test_03_AnyFilelistCollector__w_side_effects(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = setup_workdir()

    def tearDown(self):
        #cleanup_workdir(self.workdir)
        pass

    def test_01_list_and_collect__json(self):
        if E.json is None:
            return

        listfile = os.path.join(self.workdir, "filelist.json")
        data = dict(files=[dict(path=p) for p in PATHS])

        import json
        json.dump(data, open(listfile, "w"))

        config = init_config(listfile)

        fos_ref = sorted(
            f for f in (Factory.create(p, False) for p in PATHS_EXPANDED) \
        )

        filters = [
            Filters.UnsupportedTypesFilter(),
            Filters.NotExistFilter(),
            Filters.ReadAccessFilter(),
        ]
        fos_ref_filtered = [
            f for f in fos_ref if not any(filter(f) for filter in filters)
        ]

        ac = AnyFilelistCollector(listfile, config, Anycfg.CTYPE_JSON)
        self.assertTrue(isinstance(ac, AnyFilelistCollector))
        fos = ac.list(listfile)

        ac = AnyFilelistCollector(listfile, config, Anycfg.CTYPE_JSON)
        self.assertTrue(isinstance(ac, AnyFilelistCollector))
        fos_filtered = ac.collect()

        paths_in_fos = sorted(f.path for f in fos)
        paths_in_fos_filtered = sorted(f.path for f in fos_filtered)

        self.assertEquals(paths_in_fos, sorted(f.path for f in fos_ref))

        self.assertEquals(
            paths_in_fos_filtered,
            sorted(f.path for f in fos_ref_filtered)
        )


# vim:sw=4 ts=4 et:
