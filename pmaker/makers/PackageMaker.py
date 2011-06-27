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
from pmaker.shell import shell
from pmaker.utils import compile_template

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


def find_template(template, search_paths=TEMPLATE_SEARCH_PATHS):
    """Find template file from given path information.

    1. Try the path ($template)
    2. Try $path + $template where $path in $search_paths

    @param  template  Template file path may be relative to path in search paths.
    @param  search_paths  Path list to search for the template
    """
    tmpl = None

    if os.path.exists(template):
        tmpl = template
    else:
        for path in search_paths:
            t = os.path.join(path, template)

            if os.path.exists(t):
                tmpl = t
                break

    if tmpl is not None:
        logging.info("Found template: " + tmpl)

    return tmpl



class PackageMaker(object):
    """Abstract class for children to implement various packaging processes.

    TODO: Separate packaging strategy from this class. 
    (Strategy examples; autotools, simple listfile, cmake, etc.)
    """
    _type = None
    _relations = dict()
    _steps = BUILD_STEPS

    @classmethod
    def type(cls):
        return cls._type

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
        self.fileinfos = self.package["fileinfos"] = fileinfos
        self.options = options

        self.workdir = package["workdir"]
        self.destdir = package["destdir"]
        self.pname = package["name"]

        self.force = options.force
        self.upto = options.upto

        self.srcdir = os.path.join(self.workdir, "src")

        relmap = []
        if package.has_key("relations"):
            for reltype, reltargets in package["relations"]:
                rel = self._relations.get(reltype, False)
                if rel:
                    relmap.append({"type": rel, "targets": reltargets})

        self.package["relations"] = relmap

        self.package["conflicts_savedir"] = CONFLICTS_SAVEDIR % self.package
        self.package["conflicts_newdir"] = CONFLICTS_NEWDIR % self.package

    def shell(self, cmd_s):
        return shell(cmd_s, workdir=self.workdir)

    def genfile(self, template, output=False, search_paths=TEMPLATE_SEARCH_PATHS):
        """
        @param  template  Relative path of template file
        @param  output    Relative path of output to generate from template file
        """
        outfile = os.path.join(self.workdir, output or path)
        tmpl = find_template(template, search_paths)

        if tmpl is None:
            logging.warn(" Template not found in your search paths: " + template)
            return

        content = compile_template(tmpl, self.package, is_file=True)
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
        self.fileinfos = self.package["fileinfos"] = pickle.load(open(self.dumpfile()))

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

        getattr(self, step, do_nothing)() # TODO: or eval("self." + step)() ?
        self.shell("touch %s" % self.touch_file(step))

        if step == self.upto:
            if step == STEP_BUILD:
                logging.info("Successfully created packages in %s: %s" % (self.workdir, self.pname))
            sys.exit()

    def setup(self):
        for d in ("workdir", "srcdir"):
            createdir(self.package[d])

        self.copyfiles()
        self.save()

    def preconfigure(self):
        pass

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

    _type = "autotools.tgz"

    def preconfigure(self):
        if not self.package.get("fileinfos", False):
            self.load()

        self.package["distdata"] = sort_out_paths_by_dir(
            fi.target for fi in self.fileinfos if fi.isfile()
        )

        self.package["conflicted_fileinfos"] = [
            fi for fi in self.fileinfos if fi.conflicts
        ]
        self.package["not_conflicted_fileinfos"] = [
            fi for fi in self.fileinfos if not fi.conflicts
        ]

        self.genfile("autotools/configure.ac", "configure.ac")
        self.genfile("autotools/Makefile.am", "Makefile.am")
        self.genfile("common/README", "README")
        self.genfile("common/MANIFEST", "MANIFEST")
        self.genfile("common/MANIFEST.overrides", "MANIFEST.overrides")
        self.genfile("common/apply-overrides", "apply-overrides")
        self.genfile("common/revert-overrides", "revert-overrides")

    def configure(self):
        self.shell(on_debug_mode() and "autoreconf -vfi" or "autoreconf -fi")

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
