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
#
# Internal:
#
# Make some pylint errors ignored:
# pylint: disable=E0611
# pylint: disable=E1101
# pylint: disable=E1103
# pylint: disable=W0613
#
# How to run pylint: pylint --rcfile pylintrc pmaker.py
#

from distutils.sysconfig import get_python_lib
from itertools import count, groupby

from pmaker.globals import *
from pmaker.rpm import *
from pmaker.utils import *
from pmaker.xattr import *

import ConfigParser as cp
import cPickle as pickle
import copy
import datetime
import doctest
import glob
import grp
import inspect
import locale
import logging
import operator
import optparse
import os
import os.path
import platform
import pwd
import random
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest


try:
    import json
    JSON_ENABLED = True

except ImportError:
    JSON_ENABLED = False

    class json:
        @staticmethod
        def load(*args):
            return ()


__title__   = "packagemaker"
__version__ = "0.2.99"
__author__  = "Satoru SATOH"
__email__   = "satoru.satoh@gmail.com"
__website__ = "https://github.com/ssato/packagemaker"



if CHEETAH_ENABLED:
    UPTO = STEP_BUILD
else:
    UPTO = STEP_SETUP
    logging.warn("python-cheetah is not found. Packaging process can go up to \"setup\" step.")



def shell(cmd, workdir=None, dryrun=False, stop_on_error=True):
    """
    @cmd      str   command string, e.g. "ls -l ~".
    @workdir  str   in which dir to run given command?
    @dryrun   bool  if True, just print command string to run and returns.
    @stop_on_error bool  if True, RuntimeError will not be raised.

    >>> assert 0 == shell("echo ok > /dev/null")
    >>> assert 0 == shell("ls null", "/dev")
    >>> assert 0 == shell("ls null", "/dev", dryrun=True)
    >>> try:
    ...    rc = shell("ls", "/root")
    ... except RuntimeError:
    ...    pass
    >>> rc = shell("echo OK | grep -q NG 2>/dev/null", stop_on_error=False)
    """
    logging.info(" Run: %s [%s]" % (cmd, workdir))

    if dryrun:
        logging.info(" exit as we're in dry run mode.")
        return 0

    llevel = logging.getLogger().level
    if llevel < logging.WARN:
        cmd += " > /dev/null"
    elif llevel < logging.INFO:
        cmd += " 2> /dev/null"
    else:
        pass

    try:
        proc = subprocess.Popen(cmd, shell=True, cwd=workdir)
        proc.wait()
        rc = proc.returncode

    except Exception, e:
        raise RuntimeError("Error (%s) when running: %s" % (repr(e.__class__), str(e)))

    if rc == 0:
        return rc
    else:
        if stop_on_error:
            raise RuntimeError(" Failed: %s,\n rc=%d" % (cmd, rc))
        else:
            logging.error(" cmd=%s, rc=%d" % (cmd, rc))
            return rc


def createdir(targetdir, mode=0700):
    """Create a dir with specified mode.
    """
    logging.debug(" Creating a directory: %s" % targetdir)

    if os.path.exists(targetdir):
        if os.path.isdir(targetdir):
            logging.warn(" Directory already exists! Skip it: %s" % targetdir)
        else:
            raise RuntimeError(" Already exists but not a directory: %s" % targetdir)
    else:
        os.makedirs(targetdir, mode)


def rm_rf(target):
    """ "rm -rf" in python.

    >>> d = tempfile.mkdtemp(dir="/tmp")
    >>> rm_rf(d)
    >>> rm_rf(d)
    >>> 
    >>> d = tempfile.mkdtemp(dir="/tmp")
    >>> for c in "abc":
    ...     os.makedirs(os.path.join(d, c))
    >>> os.makedirs(os.path.join(d, "c", "d"))
    >>> open(os.path.join(d, "x"), "w").write("test")
    >>> open(os.path.join(d, "a", "y"), "w").write("test")
    >>> open(os.path.join(d, "c", "d", "z"), "w").write("test")
    >>> 
    >>> rm_rf(d)
    """
    if not os.path.exists(target):
        return

    if os.path.isfile(target) or os.path.islink(target):
        os.remove(target)
        return 

    warnmsg = "You're trying to rm -rf / !"
    assert target != "/", warnmsg
    assert os.path.realpath(target) != "/", warnmsg

    xs = glob.glob(os.path.join(target, "*")) + glob.glob(os.path.join(target, ".*"))

    for x in xs:
        if os.path.isdir(x):
            rm_rf(x)
        else:
            os.remove(x)

    if os.path.exists(target):
        os.removedirs(target)


def cache_needs_updates_p(cache_file, expires=0):
    if expires == 0 or not os.path.exists(cache_file):
        return True

    try:
        mtime = os.stat(cache_file).st_mtime
    except OSError:  # It indicates that the cache file cannot be updated.
        return True  # FIXME: How to handle the above case?

    cur_time = datetime.datetime.now()
    cache_mtime = datetime.datetime.fromtimestamp(mtime)

    delta = cur_time - cache_mtime  # TODO: How to do if it's negative value?

    return (delta >= datetime.timedelta(expires))


class TestFuncsWithSideEffects(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test_createdir_normal(self):
        """TODO: Check mode (permission).
        """
        d = os.path.join(self.workdir, "a")
        createdir(d)

        self.assertTrue(os.path.isdir(d))

    def test_createdir_specials(self):
        # assertIsNone is not available in python < 2.5:
        #self.assertIsNone(createdir(self.workdir))
        self.assertEquals(createdir(self.workdir), None)  # try creating dir already exists.

        f = os.path.join(self.workdir, "a")
        open(f, "w").write("test")
        self.assertRaises(RuntimeError, createdir, f)

    def test_get_compressor(self):
        _ = (_cmd, _ext, _am_opt) = get_compressor()

    def test_shell(self):
        rc = shell("echo \"\" > /dev/null", os.curdir)
        self.assertEquals(rc, 0)

        self.assertRaises(RuntimeError, shell, "grep xyz /dev/null")

        if os.getuid() != 0:
            self.assertRaises(RuntimeError, shell, "ls", "/root")

    def test_init_defaults_by_conffile_config(self):
        conf = """\
[DEFAULT]
a: aaa
b: bbb
"""
        path = os.path.join(self.workdir, "config")
        open(path, "w").write(conf)

        params = init_defaults_by_conffile(path)
        assert params["a"] == "aaa"
        assert params["b"] == "bbb"

    def test_init_defaults_by_conffile_config_and_profile_0(self):
        conf = """\
[profile0]
a: aaa
b: bbb
"""
        path = os.path.join(self.workdir, "config_p0")
        open(path, "w").write(conf)

        params = init_defaults_by_conffile(path, "profile0")
        assert params["a"] == "aaa"
        assert params["b"] == "bbb"


def distdata_in_makefile_am(paths, srcdir="src"):
    """
    @paths  file path list

    >>> ps0 = ["/etc/resolv.conf", "/etc/sysconfig/iptables"]
    >>> rs0 = [{"dir": "/etc", "files": ["src/etc/resolv.conf"], "id": "0"}, {"dir": "/etc/sysconfig", "files": ["src/etc/sysconfig/iptables"], "id": "1"}]
    >>> 
    >>> ps1 = ps0 + ["/etc/sysconfig/ip6tables", "/etc/modprobe.d/dist.conf"]
    >>> rs1 = [{"dir": "/etc", "files": ["src/etc/resolv.conf"], "id": "0"}, {"dir": "/etc/sysconfig", "files": ["src/etc/sysconfig/iptables", "src/etc/sysconfig/ip6tables"], "id": "1"}, {"dir": "/etc/modprobe.d", "files": ["src/etc/modprobe.d/dist.conf"], "id": "2"}]
    >>> 
    >>> _cmp = lambda ds1, ds2: all([utils.dicts_comp(*dt) for dt in zip(ds1, ds2)])
    >>> 
    >>> rrs0 = distdata_in_makefile_am(ps0)
    >>> rrs1 = distdata_in_makefile_am(ps1)
    >>> 
    >>> assert _cmp(rrs0, rs0), "expected %s but got %s" % (str(rs0), str(rrs0))
    >>> assert _cmp(rrs1, rs1), "expected %s but got %s" % (str(rs1), str(rrs1))
    """
    cntr = count()

    return [
        {
            "id": str(cntr.next()),
            "dir":d,
            "files": [os.path.join("src", p.strip(os.path.sep)) for p in ps]
        } \
        for d,ps in groupby(paths, os.path.dirname)
    ]


def do_nothing(*args, **kwargs):
    return


def on_debug_mode():
    return logging.getLogger().level < logging.INFO



def load_plugins(package_makers_map=PACKAGE_MAKERS):
    plugins = os.path.join(get_python_lib(), "pmaker", "*plugin*.py")
    csfx = "PackageMaker"

    for modpy in glob.glob(plugins):
        modn = os.path.basename(modpy).replace(".py")
        mod = __import__("pmaker.%s" % modn)
        pms = [c for n, c in inspect.getmembers(mod) if inspect.isclass(c) and n.endswith(csfx)]
        c.register(package_makers_map)


def do_packaging(pkg, filelist, options, pmaps=PACKAGE_MAKERS):
    cls = pmaps.get((options.type, options.format), TgzPackageMaker)
    logging.info("Use PackageMaker: %s: type=%s, format=%s" % (cls.__name__, cls.type(), cls.format()))
    cls(pkg, filelist, options).run()


def do_packaging_self(options):
    if options.pversion:
        version = options.pversion
    else:
        version = __version__

        if not options.release_build:
            version += ".%s" % date(DATE_FMT_SIMPLE)

    plugin_files = []
    if options.include_plugins:
        plugin_files = options.include_plugins.split(",")

    name = __title__
    workdir = tempfile.mkdtemp(dir="/tmp", prefix="pm-")
    summary = "A python script to build packages from existing files on your system"
    relations = "requires:python"
    packager = __author__
    mail = __email__
    url = __website__

    pkglibdir = os.path.join(workdir, get_python_lib()[1:], "pmaker")
    bindir = os.path.join(workdir, "usr", "bin")
    bin = os.path.join(bindir, "pmaker")

    filelist = os.path.join(workdir, "files.list")

    prog = sys.argv[0]

    cmd_opts = "-n %s --pversion %s -w %s --license GPLv3+ --ignore-owner " % (name, version, workdir)
    cmd_opts += " --destdir %s --no-rpmdb --url %s --upto %s" % (workdir, url, options.upto)
    cmd_opts += " --summary \"%s\" --packager \"%s\" --mail %s" % (summary, packager, mail)

    if relations:
        cmd_opts += " --relations \"%s\" " % relations

    if options.debug:
        cmd_opts += " --debug"

    if options.no_mock:
        cmd_opts += " --no-mock"

    if options.dist:
        cmd_opts += " --dist %s" % options.dist

    if options.format:
        cmd_opts += " --format %s" % options.format

    createdir(pkglibdir, mode=0755)
    shell("install -m 644 %s %s/__init__.py" % (prog, pkglibdir))

    for f in plugin_files:
        if not os.path.exists(f):
            logging.warn("Plugin %s does not found. Skip it" % f)
            continue

        nf = f.replace("pmaker-", "")
        shell("install -m 644 %s %s" % (f, os.path.join(pkglibdir, nf)))

    createdir(bindir)

    open(bin, "w").write("""\
#! /usr/bin/python
import sys, pmaker

pmaker.main(sys.argv)
""")
    shell("chmod +x %s" % bin)

    open(filelist, "w").write("""\
%s
%s/*
""" % (bin, pkglibdir))

    # @see /usr/lib/rpm/brp-python-bytecompile:
    pycompile = "import compileall, os; compileall.compile_dir(os.curdir, force=1)"
    compile_pyc = "python -c \"%s\"" % pycompile
    compile_pyo = "python -O -c \"%s\" > /dev/null" % pycompile

    shell(compile_pyc, pkglibdir)
    shell(compile_pyo, pkglibdir)

    cmd = "python %s %s %s" % (prog, cmd_opts, filelist)

    logging.info(" executing: %s" % cmd)
    os.system(cmd)


def show_examples(logs=EXAMPLE_LOGS):
    for log in logs:
        print >> sys.stdout, log


def dump_rc(rc=EXAMPLE_RC):
    print >> sys.stdout, rc



class TestMainProgram00SingleFileCases(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        target = "/etc/resolv.conf"
        self.cmd = "echo %s | python %s -n resolvconf -w %s " % (target, sys.argv[0], self.workdir)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_packaging_setup_wo_rpmdb(self):
        """Setup without rpm database
        """
        cmd = self.cmd + "--upto setup --no-rpmdb -"
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_configure_wo_rpmdb(self):
        """Configure without rpm database
        """
        cmd = self.cmd + "--upto configure --no-rpmdb -"
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_sbuild_wo_rpmdb_wo_mock(self):
        """Build src package without rpm database without mock
        """
        cmd = self.cmd + "--upto sbuild --no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.src.rpm" % self.workdir)) > 0)

    def test_packaging_build_rpm_wo_rpmdb_wo_mock(self):
        """Build package without rpm database without mock
        """
        cmd = self.cmd + "--upto build --no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_wo_rpmdb_wo_mock(self):
        """Build package without rpm database without mock (no --upto option)
        """
        cmd = self.cmd + "--no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_with_relations_wo_rpmdb_wo_mock(self):
        """Build package with some additional relations without rpm database
        without mock (no --upto option).
        """
        cmd = self.cmd + "--relations \"requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old\" "
        cmd += "--no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

        rpmspec = glob.glob("%s/*/*.spec" % self.workdir)[0]
        cmds = (
            "grep -q -e '^Requires:.*bash, zsh' %s" % rpmspec,
            "grep -q -e '^Obsoletes:.*sysdata' %s" % rpmspec,
            "grep -q -e '^Conflicts:.*sysdata-old' %s" % rpmspec,
        )

        for cmd in cmds:
            self.assertEquals(os.system(cmd), 0)

    def test_packaging_symlink_wo_rpmdb_wo_mock(self):
        idir = os.path.join(self.workdir, "var", "lib", "net")
        os.makedirs(idir)
        os.symlink("/etc/resolv.conf", os.path.join(idir, "resolv.conf"))

        cmd = "echo %s/resolv.conf | python %s -n resolvconf -w %s --no-rpmdb --no-mock -" % (idir, sys.argv[0], self.workdir)

        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_wo_rpmdb_wo_mock_with_destdir(self):
        destdir = os.path.join(self.workdir, "destdir")
        createdir(os.path.join(destdir, "etc"))
        shell("cp /etc/resolv.conf %s/etc" % destdir)

        cmd = "echo %s/etc/resolv.conf | python %s -n resolvconf -w %s --no-rpmdb --no-mock --destdir=%s -" % \
            (destdir, sys.argv[0], self.workdir, destdir)

        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_wo_rpmdb_wo_mock_with_compressor(self):
        (zcmd, _zext, _z_am_opt) = get_compressor()

        if zcmd == "xz":
            zchoices = ["bz2", "gz"]

        elif zcmd == "bzip2":
            zchoices = ["gz"]

        else:
            return  # only "gz" is available and cannot test others.

        for z in zchoices:
            cmd = self.cmd + "--no-rpmdb --no-mock --upto sbuild --compressor %s -" % z

            self.assertEquals(os.system(cmd), 0)

            archives = glob.glob("%s/*/*.tar.%s" % (self.workdir, z))
            self.assertFalse(archives == [], "failed with --compressor " + z)

            if z != zchoices[-1]:
                for x in glob.glob("%s/*" % self.workdir):
                    rm_rf(x)

    def test_packaging_with_rpmdb_wo_mock(self):
        cmd = self.cmd + "--no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_with_rpmdb_with_mock(self):
        network_avail = os.system("ping -q -c 1 -w 1 github.com > /dev/null 2> /dev/null") == 0

        if not network_avail:
            logging.warn("Network does not look available right now. Skip this test.")
            return

        cmd = self.cmd + "-"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_deb(self):
        """'dh' may not be found on this system so that it will only go up to
        "configure" step.
        """
        cmd = self.cmd + "--upto configure --format deb --no-rpmdb -"
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_with_rc(self):
        rc = os.path.join(self.workdir, "rc")
        prog = sys.argv[0]

        #PMAKERRC=./pmakerrc.sample python pmaker.py files.list --upto configure
        cmd = "python %s --dump-rc > %s" % (prog, rc)
        self.assertEquals(os.system(cmd), 0)

        cmd = "echo /etc/resolv.conf | PMAKERRC=%s python %s -w %s --upto configure -" % (rc, prog, self.workdir)
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_wo_rpmdb_wo_mock_with_a_custom_template(self):
        global TEMPLATES

        prog = sys.argv[0]
        tmpl0 = os.path.join(self.workdir, "package.spec")

        open(tmpl0, "w").write(TEMPLATES["package.spec"])

        cmd = self.cmd + "--no-rpmdb --no-mock --templates=\"package.spec:%s\" -" % tmpl0
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.src.rpm" % self.workdir)) > 0)



class TestMainProgram01JsonFileCases(unittest.TestCase):

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
            "gid": 0
        }
    }
]
"""
        self.listfile = os.path.join(self.workdir, "filelist.json")
        self.cmd = "python %s -n resolvconf -w %s --itype filelist.json " % (sys.argv[0], self.workdir)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_packaging_with_rpmdb_wo_mock(self):
        f = open(self.listfile, "w")
        f.write(self.json_data)
        f.close()

        cmd = self.cmd + "--no-mock " + self.listfile
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)



class TestMainProgram01MultipleFilesCases(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        self.filelist = os.path.join(self.workdir, "file.list")

        targets = [
            "/etc/auto.*", "/etc/modprobe.d/*", "/etc/resolv.conf",
            "/etc/security/limits.conf", "/etc/security/access.conf",
            "/etc/grub.conf", "/etc/system-release", "/etc/skel",
        ]
        self.files = [f for f in targets if os.path.exists(f)]

    def tearDown(self):
        rm_rf(self.workdir)

    def test_packaging_build_rpm_wo_mock(self):
        open(self.filelist, "w").write("\n".join(self.files))

        cmd = "python %s -n etcdata -w %s --upto build --no-mock %s" % (sys.argv[0], self.workdir, self.filelist)
        self.assertEquals(os.system(cmd), 0)
        self.assertEquals(len(glob.glob("%s/*/*.src.rpm" % self.workdir)), 1)
        self.assertEquals(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)), 2) # etcdata and etcdata-overrides



def run_doctests(verbose):
    doctest.testmod(verbose=verbose, raise_on_error=True)


def run_unittests(verbose, test_choice):
    def tsuite(testcase):
        return unittest.TestLoader().loadTestsFromTestCase(testcase)

    basic_tests = [
        TestDecoratedFuncs,
        TestFuncsWithSideEffects,
        TestFileInfoFactory,
        TestRpmFileInfoFactory,
        TestFileOperations,
        TestDirOperations,
        TestSymlinkOperations,
        TestMiscFunctions,
        TestDestdirModifier,
        TestOwnerModifier,
        TestTargetAttributeModifier,
        TestFilelistCollector,
        TestExtFilelistCollector,
        TestJsonFilelistCollector,
    ]

    system_tests = [
        TestRpm,
        TestMainProgram00SingleFileCases,
        TestMainProgram01JsonFileCases,
        TestMainProgram01MultipleFilesCases,
    ]

    (major, minor) = sys.version_info[:2]

    suites = [tsuite(c) for c in basic_tests]

    if test_choice == TEST_FULL:
        suites += [tsuite(c) for c in system_tests]

    tests = unittest.TestSuite(suites)

    if major == 2 and minor < 5:
        unittest.TextTestRunner().run(tests)
    else:
        unittest.TextTestRunner(verbosity=(verbose and 2 or 0)).run(tests)


def run_alltests(verbose, test_choice):
    run_doctests(verbose)
    run_unittests(verbose, test_choice)


def parse_conf_value(s):
    """Simple and naive parser to parse value expressions in config files.

    >>> assert 0 == parse_conf_value("0")
    >>> assert 123 == parse_conf_value("123")
    >>> assert True == parse_conf_value("True")
    >>> assert [1,2,3] == parse_conf_value("[1,2,3]")
    >>> assert "a string" == parse_conf_value("a string")
    >>> assert "0.1" == parse_conf_value("0.1")
    """
    intp = re.compile(r"^([0-9]|([1-9][0-9]+))$")
    boolp = re.compile(r"^(true|false)$", re.I)
    listp = re.compile(r"^(\[\s*((\S+),?)*\s*\])$")

    def matched(pat, s):
        m = pat.match(s)
        return m is not None

    if not s:
        return ""

    if matched(boolp, s):
        return bool(s)

    if matched(intp, s):
        return int(s)

    if matched(listp, s):
        return eval(s)  # TODO: too danger. safer parsing should be needed.

    return s


def parse_template_list_str(templates):
    """
    simple parser for options.templates.

    >>> assert parse_template_list_str("") == {}
    >>> assert parse_template_list_str("a:b") == {"a": "b"}
    >>> assert parse_template_list_str("a:b,c:d") == {"a": "b", "c": "d"}
    """
    if templates:
        return dict(kv.split(":") for kv in templates.split(","))
    else:
        return dict()


def init_defaults_by_conffile(config=None, profile=None, prog="pmaker"):
    """
    Initialize default values for options by loading config files.
    """
    if config is None:
        home = os.environ.get("HOME", os.curdir) # Is there case that $HOME is empty?

        confs = ["/etc/%s.conf" % prog]
        confs += sorted(glob.glob("/etc/%s.d/*.conf" % prog))
        confs += [os.environ.get("%sRC" % prog.upper(), os.path.join(home, ".%src" % prog))]
    else:
        confs = (config,)

    cparser = cp.SafeConfigParser()
    loaded = False

    for c in confs:
        if os.path.exists(c):
            logging.info("Loading config: %s" % c)
            cparser.read(c)
            loaded = True

    if not loaded:
        return {}

    if profile:
        defaults = dict((k, parse_conf_value(v)) for k,v in cparser.items(profile))
    else:
        defaults = cparser.defaults()

#    for sec in cparser.sections():
#        defaults.update(dict(((k, parse_conf_value(v)) for k, v in cparser.items(sec))))

    return defaults


def option_parser(V=__version__, pmaps=PACKAGE_MAKERS, itypes=COLLECTORS,
        test_choices=TEST_CHOICES, steps=BUILD_STEPS,
        compressors=COMPRESSORS, upto=UPTO):

    ver_s = "%prog " + V

    upto_params = {
        "choices": [name for name, _logmsg, helptxt in steps],
        "choices_str": ", ".join(("%s (%s)" % (name, helptxt) for name, _logmsg, helptxt in steps)),
        "default": upto,
    }

    pdriver = unique([tf[0] for tf in pmaps.keys()])
    pdriver_help = "Package driver type: " + ", ".join(pdriver) + " [%default]"

    pformats = unique([tf[1] for tf in pmaps.keys()])
    pformats_help = "Package format: " + ", ".join(pformats) + " [%default]"

    itypes = sorted(itypes.keys())
    itypes_help = "Input type: " + ", ".join(itypes) + " [%default]"

    mail = get_email()
    packager = get_fullname()
    dist = "fedora-14-%s" % get_arch()

    compressor = get_compressor(compressors)  # cmd, extension, am_option,
    compressor_choices = [ext for _c, ext, _a in compressors]

    workdir = os.path.join(os.path.abspath(os.curdir), "workdir")

    cds = init_defaults_by_conffile()

    defaults = {
        "workdir": cds.get("workdir", workdir),
        "upto": cds.get("upto", upto_params["default"]),
        "type": cds.get("type", "filelist"),
        "format": cds.get("format", "rpm"),
        "itype": cds.get("itype", "filelist"),
        "compressor": cds.get("compressor", compressor[1]),
        "verbose": cds.get("verbose", False),
        "quiet": cds.get("quiet", False),
        "debug": cds.get("debug", False),
        "ignore_owner": cds.get("ignore_owner", False),
        "destdir": cds.get("destdir", ""),
        "link": cds.get("link", False),
        "with_pyxattr": cds.get("with_pyxattr", False),

        "name": cds.get("name", ""),
        "pversion": cds.get("pversion", "0.1"),
        "group": cds.get("group", "System Environment/Base"),
        "license": cds.get("license", "GPLv2+"),
        "url": cds.get("url", "http://localhost.localdomain"),
        "summary": cds.get("summary", ""),
        "arch": cds.get("arch", False),
        "relations": cds.get("relations", ""),
        "packager": cds.get("packager", packager),
        "mail": cds.get("mail", mail),

        "scriptlets": cds.get("scriptlets", ""),
        "changelog": cds.get("changelog", ""),

         # TODO: Detect appropriate distribution (for mock) automatically.
        "dist": cds.get("dist", dist),
        "no_rpmdb": cds.get("no_rpmdb", False),
        "no_mock": cds.get("no_mock", False),

        "force": False,

        # these are not in conf file:
        "show_examples": False,
        "dump_rc": False,
        "tests": False,
        "tlevel": test_choices[0],
        "build_self": False,
        "profile": False,

        "release_build": False,
        "include_plugins": ",".join(glob.glob("pmaker-plugin-*.py")),
    }

    p = optparse.OptionParser("""%prog [OPTION ...] FILE_LIST

Arguments:

  FILE_LIST  a file contains absolute file paths list or "-" (read paths list
             from stdin).

             The lines starting with "#" in the list file are ignored.

             The "*" character in lines will be treated as glob pattern and
             expanded to the real file names list.

Environment Variables:

  PMAKERRC    Configuration file path. see also: `%prog --dump-rc`

Examples:
  %prog -n foo files.list
  cat files.list | %prog -n foo -  # same as above.

  %prog -n foo --pversion 0.2 -l MIT files.list
  %prog -n foo --relations "requires:httpd,/sbin/service;obsoletes:foo-old" files.list

  %prog --tests --debug  # run test suites

  %prog --build-self    # package itself

  see the output of `%prog --show-examples` for more detailed examples.""",
    version=ver_s
    )
    
    p.set_defaults(**defaults)

    bog = optparse.OptionGroup(p, "Build options")
    bog.add_option("-w", "--workdir", help="Working dir to dump outputs [%default]")
    bog.add_option("", "--upto", type="choice", choices=upto_params["choices"],
        help="Which packaging step you want to proceed to: " + upto_params["choices_str"] + " [Default: %default]")
    bog.add_option("", "--driver", type="choice", choices=pdriver, help=pdriver_help)
    bog.add_option("", "--format", type="choice", choices=pformats, help=pformats_help)
    bog.add_option("", "--itype", type="choice", choices=itypes, help=itypes_help)
    bog.add_option("", "--destdir", help="Destdir (prefix) you want to strip from installed path [%default]. "
        "For example, if the target path is \"/builddir/dest/usr/share/data/foo/a.dat\", "
        "and you want to strip \"/builddir/dest\" from the path when packaging \"a.dat\" and "
        "make it installed as \"/usr/share/foo/a.dat\" with the package , you can accomplish "
        "that by this option: \"--destdir=/builddir/destdir\"")
    bog.add_option("", "--templates", help="Use custom template files. "
        "TEMPLATES is a comma separated list of template output and file after the form of "
        "RELATIVE_OUTPUT_PATH_IN_SRCDIR:TEMPLATE_FILE such like \"package.spec:/tmp/foo.spec.tmpl\", "
        "and \"debian/rules:mydebrules.tmpl, Makefile.am:/etc/foo/mymakefileam.tmpl\". "
        "Supported template syntax is Python Cheetah: http://www.cheetahtemplate.org .")
    bog.add_option("", "--link", action="store_true", help="Make symlinks for symlinks instead of copying them")
    bog.add_option("", "--with-pyxattr", action="store_true", help="Get/set xattributes of files with pure python code.")
    p.add_option_group(bog)

    pog = optparse.OptionGroup(p, "Package metadata options")
    pog.add_option("-n", "--name", help="Package name [%default]")
    pog.add_option("", "--group", help="The group of the package [%default]")
    pog.add_option("", "--license", help="The license of the package [%default]")
    pog.add_option("", "--url", help="The url of the package [%default]")
    pog.add_option("", "--summary", help="The summary of the package")
    pog.add_option("-z", "--compressor", type="choice", choices=compressor_choices,
        help="Tool to compress src archives [%default]")
    pog.add_option("", "--arch", action="store_true", help="Make package arch-dependent [false - noarch]")
    pog.add_option("", "--relations",
        help="Semicolon (;) separated list of a pair of relation type and targets "
        "separated with comma, separated with colon (:), "
        "e.g. \"requires:curl,sed;obsoletes:foo-old\". "
        "Expressions of relation types and targets are varied depends on "
        "package format to use")
    pog.add_option("", "--packager", help="Specify packager's name [%default]")
    pog.add_option("", "--mail", help="Specify packager's mail address [%default]")
    pog.add_option("", "--pversion", help="Specify the package version [%default]")
    pog.add_option("", "--ignore-owner", action="store_true", help="Ignore owner and group of files and then treat as root's")
    pog.add_option("", "--changelog", help="Specify text file contains changelog")
    p.add_option_group(pog)

    rog = optparse.OptionGroup(p, "Options for rpm")
    rog.add_option("", "--dist", help="Target distribution (for mock) [%default]")
    rog.add_option("", "--no-rpmdb", action="store_true", help="Do not refer rpm db to get extra information of target files")
    rog.add_option("", "--no-mock", action="store_true", help="Build RPM with only using rpmbuild (not recommended)")
    rog.add_option("", "--scriptlets", help="Specify the file contains rpm scriptlets")
    p.add_option_group(rog)

    sog = optparse.OptionGroup(p, "Self-build options")
    sog.add_option("", "--release-build", action="store_true", help="Make a release build")
    sog.add_option("", "--include-plugins", help="Comma separated list of plugin files to be included in dist.")
    p.add_option_group(sog)

    tog = optparse.OptionGroup(p, "Test options")
    tog.add_option("", "--tests", action="store_true", help="Run tests.")
    tog.add_option("", "--tlevel", type="choice", choices=test_choices,
        help="Select the level of tests to run. Choices are " + ", ".join(test_choices) + " [%default]")
    tog.add_option("", "--profile", action="store_true", help="Enable profiling")
    p.add_option_group(tog)

    p.add_option("", "--force", action="store_true", help="Force going steps even if the steps looks done")
    p.add_option("-v", "--verbose", action="store_true", help="Verbose mode")
    p.add_option("-q", "--quiet", action="store_true", help="Quiet mode")
    p.add_option("-D", "--debug", action="store_true", help="Debug mode")

    p.add_option("", "--build-self", action="store_true", help="Package itself (self-build)")
    p.add_option("", "--show-examples", action="store_true", help="Show examples")
    p.add_option("", "--dump-rc", action="store_true", help="Show conf file example")

    return p


def relations_parser(relations_str):
    """
    >>> relations_parser("requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old")
    [('requires', ['bash', 'zsh']), ('obsoletes', ['sysdata']), ('conflicts', ['sysdata-old'])]
    """
    if not relations_str:
        return []

    rels = [rel.split(":") for rel in relations_str.split(";")]
    return [(reltype, reltargets.split(",")) for reltype, reltargets in rels]


def main(argv=sys.argv, compressors=COMPRESSORS, templates=TEMPLATES):
    global TEMPLATES, PYXATTR_ENABLED

    verbose_test = False

    loglevel = logging.INFO
    logdatefmt = "%H:%M:%S" # too much? "%a, %d %b %Y %H:%M:%S"
    logformat = "%(asctime)s [%(levelname)-4s] %(message)s"

    logging.basicConfig(level=loglevel, format=logformat, datefmt=logdatefmt)

    pkg = dict()

    p = option_parser()
    (options, args) = p.parse_args(argv[1:])

    if options.show_examples:
        show_examples()
        sys.exit(0)

    if options.dump_rc:
        dump_rc()
        sys.exit(0)

    if options.verbose:
        logging.getLogger().setLevel(logging.INFO)
        verbose_test = False
    else:
        logging.getLogger().setLevel(logging.WARNING)
        verbose_test = False

    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        verbose_test = True

    if options.build_self:
        if options.tests:
            rc = os.system("python %s --tests --tlevel=full -v" % argv[0])
            if rc != 0:
                sys.exit(rc)

        do_packaging_self(options)
        sys.exit()

    if options.tests:
        if options.profile:
            import cProfile as profile
            # FIXME: how to do? -  python <self> -m cProfile ...
            print >> sys.stderr, \
                "Not implemented yet. run \"python %s -m cProfile --tests ...\" instead" % \
                        (argv[0], options.tlevel)
            sys.exit()
        else:
            run_alltests(verbose_test, options.tlevel)
        sys.exit()

    if len(args) < 1:
        p.print_usage()
        sys.exit(1)

    filelist = args[0]

    pkg["noarch"] = not options.arch

    if options.templates:
        for tgt, tmpl in parse_template_list_str(options.templates).iteritems():
            if templates.has_key(tgt):
                try:
                    tmpl_content = open(tmpl).read()
                except:
                    logging.warn(" Could not open the template: " + tmpl)
                    tmpl_content = templates[tgt]

                templates[tgt] = tmpl_content
            else:
                logging.warn(" target output %s is not defined in template list" % tgt)

    if options.scriptlets:
        try:
            scriptlets = open(options.scriptlets).read()
        except IOError:
            logging.warn(" Could not open %s to read scriptlets" % options.scriptlets)
            scriptlets = ""

        pkg["scriptlets"] = scriptlets

    if not options.name:
        print >> sys.stderr, "You must specify the package name with \"--name\" option"
        sys.exit(-1)

    pkg["name"] = options.name
    pkg["release"] = "1"
    pkg["group"] = options.group
    pkg["license"] = options.license
    pkg["url"] = options.url

    pkg["version"] = options.pversion
    pkg["packager"] = options.packager
    pkg["mail"] = options.mail

    pkg["workdir"] = os.path.abspath(os.path.join(options.workdir, "%(name)s-%(version)s" % pkg))
    pkg["srcdir"] = os.path.join(pkg["workdir"], "src")

    compressor_am_opt = [am_opt for _c, _ext, am_opt in compressors if _ext == options.compressor][0]

    pkg["compressor"] = {
        "ext": options.compressor,
        "am_opt": compressor_am_opt,
    }

    if options.relations:
        pkg["relations"] = relations_parser(options.relations)

    pkg["dist"] = options.dist

    # TODO: Revert locale setting change just after timestamp was gotten.
    locale.setlocale(locale.LC_ALL, "C")
    pkg["date"] = {
        "date": date(DATE_FMT_RFC2822),
        "timestamp": date(),
    }
    pkg["host"] = hostname()

    pkg["format"] = options.format

    if options.link:
        SymlinkOperations.link_instead_of_copy = True

    if options.with_pyxattr:
        if not PYXATTR_ENABLED:
            logging.warn(" pyxattr module is not found so that it will not be used.")
    else:
        PYXATTR_ENABLED = False

    pkg["destdir"] = options.destdir.rstrip(os.path.sep)

    if options.summary:
        pkg["summary"] = options.summary
    else:
        pkg["summary"] = "Custom package of " + options.name

    if options.changelog:
        try:
            changelog = open(options.changelog).read()
        except IOError:
            logging.warn(" Could not open %s to read changelog" % options.changelog)
            changelog = ""

        pkg["changelog"] = changelog
    else:
        pkg["changelog"] = ""

    do_packaging(pkg, filelist, options)


if __name__ == '__main__':
    main()

# vim: set sw=4 ts=4 expandtab:
