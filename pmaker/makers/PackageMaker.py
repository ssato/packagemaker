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
from itertools import count, groupby

from pmaker.globals import *
from pmaker.rpm import *
from pmaker.utils import *

import cPickle as pickle
import logging
import os
import os.path
import sys


if CHEETAH_ENABLED:
    UPTO = STEP_BUILD
else:
    UPTO = STEP_SETUP
    logging.warn("python-cheetah is not found. Packaging process can go up to \"setup\" step.")


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
    """Abstract class for classes to implement various packaging processes.
    """
    global BUILD_STEPS, TEMPLATES, COLLECTORS

    _templates = TEMPLATES
    _type = "filelist"
    _format = None
    _collector = FilelistCollector
    _relations = {}

    _collector_maps = COLLECTORS

    _steps = BUILD_STEPS

    @classmethod
    def register(cls, pmmaps=PACKAGE_MAKERS):
        pmmaps[(cls.type(), cls.format())] = cls

    @classmethod
    def templates(cls):
        return cls._templates

    @classmethod
    def type(cls):
        return cls._type

    @classmethod
    def format(cls):
        return cls._format

    def collector(self):
        return self._collector

    def __init__(self, package, filelist, options, *args, **kwargs):
        self.package = package
        self.filelist = filelist
        self.options = options

        self.workdir = package["workdir"]
        self.destdir = package["destdir"]
        self.pname = package["name"]

        self.force = options.force
        self.upto = options.upto

        self.srcdir = os.path.join(self.workdir, "src")

        self._collector = self._collector_maps.get(options.itype, FilelistCollector)
        logging.info("Use Collector: %s (%s)" % (self._collector.__name__, options.itype))

        relmap = []
        if package.has_key("relations"):
            for reltype, reltargets in package["relations"]:
                rel = self._relations.get(reltype, False)
                if rel:
                    relmap.append({"type": rel, "targets": reltargets})

        self.package["relations"] = relmap

        self.package["conflicts_savedir"] = CONFLICTS_SAVEDIR % self.package
        self.package["conflicts_newdir"] = CONFLICTS_NEWDIR % self.package

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def shell(self, cmd_s):
        return shell(cmd_s, workdir=self.workdir)

    def to_srcdir(self, path):
        return to_srcdir(self.srcdir, path)

    def genfile(self, path, output=False):
        outfile = os.path.join(self.workdir, (output or path))
        open(outfile, "w").write(compile_template(self.templates()[path], self.package))

    def copyfiles(self):
        for fi in self.package["fileinfos"]:
            fi.copy(os.path.join(self.workdir, self.to_srcdir(fi.target)), self.force)

    def dumpfile_path(self):
        return os.path.join(self.workdir, "pmaker-package-filelist.pkl")

    def save(self, pkl_proto=pickle.HIGHEST_PROTOCOL):
        pickle.dump(self.package["fileinfos"], open(self.dumpfile_path(), "wb"), pkl_proto)

    def load(self):
        self.package["fileinfos"] = pickle.load(open(self.dumpfile_path()))

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

    def collect(self, *args, **kwargs):
        collector = self.collector()(self.filelist, self.package["name"], self.options)
        return collector.collect()

    def setup(self):
        self.package["fileinfos"] = self.collect()

        for d in ("workdir", "srcdir"):
            createdir(self.package[d])

        self.copyfiles()
        self.save()

    def preconfigure(self):
        if not self.package.get("fileinfos", False):
            self.load()

        self.package["distdata"] = distdata_in_makefile_am(
            [fi.target for fi in self.package["fileinfos"] if fi.type() == TYPE_FILE]
        )

        self.package["conflicted_fileinfos"] = [fi for fi in self.package["fileinfos"] if fi.conflicts]
        self.package["not_conflicted_fileinfos"] = [fi for fi in self.package["fileinfos"] if not fi.conflicts]

        _dirname = lambda fi: os.path.dirname(fi.original_path)
        self.package["conflicted_fileinfos_groupby_dir"] = \
            [(dir, list(fis_g)) for dir, fis_g in groupby(self.package["conflicted_fileinfos"], _dirname)]

        self.genfile("configure.ac")
        self.genfile("Makefile.am")
        self.genfile("README")
        self.genfile("MANIFEST")
        self.genfile("MANIFEST.overrides")
        self.genfile("apply-overrides")
        self.genfile("revert-overrides")

    def configure(self):
        if on_debug_mode():
            self.shell("autoreconf -vfi")
        else:
            self.shell("autoreconf -fi")

    def sbuild(self):
        if on_debug_mode():
            self.shell("./configure --quiet")
            self.shell("make")
            self.shell("make dist")
        else:
            self.shell("./configure --quiet --enable-silent-rules")
            self.shell("make V=0 > /dev/null")
            self.shell("make dist V=0 > /dev/null")

    def build(self):
        pass

    def run(self):
        """run all of the packaging processes: setup, configure, build, ...
        """
        d = {"workdir": self.workdir, "pname": self.pname}

        for step, msgfmt, _helptxt in self._steps:
            logging.info(msgfmt % d)
            self.try_the_step(step)



class TgzPackageMaker(PackageMaker):
    _format = "tgz"


TgzPackageMaker.register()

# vim: set sw=4 ts=4 expandtab:
