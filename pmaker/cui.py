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

from pmaker.globals import *
from pmaker.rpmutils import *
from pmaker.utils import *

import ConfigParser as cp
import glob
import inspect
import locale
import logging
import optparse
import os
import os.path
import sys


__title__   = "packagemaker"
__version__ = "0.2.99"
__author__  = "Satoru SATOH"
__email__   = "satoru.satoh@gmail.com"
__website__ = "https://github.com/ssato/packagemaker"



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
