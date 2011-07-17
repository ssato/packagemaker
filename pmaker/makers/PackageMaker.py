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
from pmaker.globals import *
from pmaker.utils import *
from pmaker.shell import shell
from pmaker.environ import hostname
from pmaker.package import Package

import cPickle as pickle
import itertools
import logging
import os
import os.path
import sys



def to_srcdir(srcdir, path):
    """
    >>> srcdir = "/tmp/w/src"
    >>> assert to_srcdir(srcdir, "/a/b/c") == "/tmp/w/src/a/b/c"
    >>> assert to_srcdir(srcdir, "a/b") == "/tmp/w/src/a/b"
    >>> assert to_srcdir(srcdir, "/") == "/tmp/w/src/"
    """
    assert path != "", "Empty path was given"

    return os.path.join(srcdir, path.strip(os.path.sep))



class PackageMaker(object):
    """Abstract class for children to implement various packaging processes.

    TODO: Separate packaging strategy from this class. 
    (Strategy examples; autotools, simple listfile, cmake, etc.)
    """
    _format = None
    _scheme = None
    _relations = dict()
    _steps = BUILD_STEPS
    _templates = dict((
        # (generated_file_in_relative_path, template_in_relative_path),
        # ("configure.ac", "autotools/configure.ac"),
    ))

    @classmethod
    def format(cls):
        return cls._format

    @classmethod
    def type(cls):
        return "%s.%s" % (cls._scheme, cls._format)

    @classmethod
    def register(cls, pmakers=PACKAGE_MAKERS):
        if not pmakers.get(cls.type(), False):
            pmakers[cls.type()] = cls

    def __init__(self, package, fileinfos, options):
        """
        @param  package    Dict holding package's metadata
        @param  fileinfos  Target FileInfo objects :: [FileInfo]
        @param  options    Command line options :: optparse.Option  (FIXME)
        """
        self.package = package
        self.fileinfos = self.package.fileinfos = fileinfos
        self.options = options

        self.force = options.force
        self.upto = options.upto
        self.template_paths = options.template_paths

        for k in ("workdir", "destdir", "srcdir"): 
            setattr(self, k, getattr(package, k, None))

        self.pname = package.name

        self.package.format = self.format()

        rels = [(self._relations.get(t, False), ts) for t, ts in options.relations]
        relmap = [dict(type=t, targets=ts) for t, ts in rels if t]
        self.package.relations = relmap

    def templates(self):
        for k, v in self._templates.iteritems():
            yield (v, k)  # v: template, k: file to be generated

    def shell(self, cmd_s):
        return shell(cmd_s, workdir=self.workdir)

    def genfile(self, template, output=False):
        """
        @param  template  Relative path of template file
        @param  output    Relative path of output to generate from template file
        """
        outfile = os.path.join(self.workdir, output or path)
        tmpl = find_template(template, self.template_paths)

        if tmpl is None:
            logging.warn(" Template not found in your search paths: " + template)
            return

        content = compile_template(tmpl, self.package.as_dict(), is_file=True)
        open(outfile, "w").write(content)

    def copyfiles(self):
        for fi in self.fileinfos:
            dest = to_srcdir(self.srcdir, fi.target)
            fi.copy(dest, self.force)

    def dumpfile(self):
        return os.path.join(self.workdir, "pmaker-package-listfile.pkl")

    def save(self, proto=pickle.HIGHEST_PROTOCOL):
        pickle.dump(
            self.fileinfos,
            open(self.dumpfile(), "wb"),
            proto
        )

    def load(self):
        try:
            f = open(self.dumpfile())
            fis = pickle.load(f)

            if fis:
                self.fileinfos = self.package.fileinfos = fis
        except Exception, e:
            logging.warn(str(e))

    def touch_file(self, step):
        return os.path.join(self.workdir, "pmaker-%s.stamp" % step)

    def try_the_step(self, step):
        if os.path.exists(self.touch_file(step)):
            msg = "...The step looks already done"

            if self.force:
                logging.info(msg + ": " + step)
            else:
                logging.info(msg + ". Skip the step: " + step)
                return

        getattr(self, step, do_nothing)()
        self.shell("touch %s" % self.touch_file(step))

        if step == self.upto:
            if step == STEP_BUILD:
                logging.info("Successfully created packages in %s: %s" % (self.workdir, self.pname))
            sys.exit()

    def setup(self):
        createdir(self.workdir)
        createdir(self.srcdir)

        self.copyfiles()
        self.save()

    def preconfigure(self):
        for tmpl, out in self.templates():
            self.genfile(tmpl, out)

    def configure(self):
        pass

    def sbuild(self):
        pass

    def build(self):
        pass

    def run(self):
        """run all of the packaging processes: setup, configure, build, ...
        """
        d = dict(workdir=self.workdir, pname=self.pname)

        for step, msgfmt, _helptxt in self._steps:
            logging.info(msgfmt % d)
            self.try_the_step(step)



class AutotoolsTgzPackageMaker(PackageMaker):

    _format = "tgz"
    _scheme = "autotools"
    _templates = dict((
        ("configure.ac", "autotools/configure.ac"),
        ("Makefile.am", "autotools/Makefile.am"),
        ("README", "common/README"),
        ("MANIFEST", "common/manifest"),
        ("MANIFEST.overrides", "common/manifest.overrides"),
        ("apply-overrides", "common/apply-overrides"),
        ("revert-overrides", "common/revert-overrides"),
    ))

    def preconfigure(self):
        if not self.package.fileinfos:
            self.load()

        self.package.distdata = sort_out_paths_by_dir(
            fi.target for fi in self.fileinfos if fi.isfile()
        )

        self.package.conflicted_fileinfos = [
            fi for fi in self.fileinfos if getattr(fi, "conflicts", False)
        ]
        self.package.not_conflicted_fileinfos = [
            fi for fi in self.fileinfos if not getattr(fi, "conflicts", False)
        ]

        super(AutotoolsTgzPackageMaker, self).preconfigure()

    def configure(self):
        logfile = os.path.join(self.workdir, "pmaker.configure.log")
        self.shell(
            on_debug_mode() and "autoreconf -vfi" or "autoreconf -fi > " + logfile
        )

    def sbuild(self):
        if on_debug_mode():
            self.shell("./configure --quiet")
            self.shell("make")
            self.shell("make dist")
        else:
            self.shell("./configure --quiet --enable-silent-rules")
            self.shell("make V=0 > /dev/null")
            self.shell("make dist V=0 > /dev/null")



def init():
    AutotoolsTgzPackageMaker.register()


# vim: set sw=4 ts=4 expandtab:
