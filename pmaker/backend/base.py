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
from pmaker.globals import PACKAGING_STEPS, STEP_BUILD
from pmaker.models.Bunch import Bunch

import pmaker.backend.utils as PU
import pmaker.shell as S
import pmaker.tenjinwrapper as T
import pmaker.utils as U

import cPickle as pickle
import logging
import os.path
import sys


class Base(object):
    """
    Abstract class for children to implement packaging backends.
    """
    _format = None  # packaging format, e.g. rpm, deb.
    _strategy = None  # packaging strategy, e.g. autotools.single.

    _steps = PACKAGING_STEPS  # packaging (build) steps to run.

    # Relations between packages :: { relation_key: package_specific_repr }
    _relations = {
        # e.g. "requires": "Requires",
        #      "requires.pre": "Requires(pre)",
        #      "conflicts": "Conflicts",
    }

    # Templates in the form of [(tmpl, out)] where tmpl is the path of template
    # file relative to template search paths, and out is the path of output
    # file relative to workdir.
    _templates = [
        # (<template_path>, <template instance path relative to src topdir>)
        # e.g. ("1/autotools.single/configure.ac": "configure.ac"),
    ]

    @classmethod
    def format(cls):
        return cls._format

    @classmethod
    def strategy(cls):
        return cls._strategy

    @classmethod
    def type(cls):
        return "%s.%s" % (cls.strategy(), cls.format())

    def relations_maps(self, rels):
        return [
            Bunch(type=t, targets=ts) for t, ts in \
                [(self._relations.get(x, None), xs) for x, xs in rels] \
                    if t is not None
        ]

    def __setup_aliases(self, pkgdata):
        self.files = pkgdata.files
        self.workdir = pkgdata.workdir
        self.destdir = pkgdata.destdir
        self.srcdir = pkgdata.srcdir
        self.stepto = pkgdata.stepto
        self.template_paths = pkgdata.template_paths
        self.force = pkgdata.force

    def logfile(self, name):
        return os.path.join(self.workdir, "pmaker.%s.log" % name)

    def __init__(self, pkgdata, **kwargs):
        """
        :param pkgdata:  Object holding all data and metadata for packaging
        """
        self.pkgdata = pkgdata
        self.pkgdata.format = self.format()  # override it.

        self.__setup_aliases(pkgdata)
        #self.pkgdata.relations = self.relations_maps(pkgdata.relations)

        for k, v in kwargs.iteritems():
            if getattr(self, k, None) is None:
                setattr(self, k, v)

    def shell(self, cmd_s, workdir=None, **kwargs):
        """
        Run shell command.
        """
        if workdir is None:
            workdir = self.workdir

        return S.run(cmd_s, workdir=workdir, **kwargs)

    def genfile(self, template, output):
        """
        Generate file in workdir from given template.

        :param template:  Template file path relative to search dirs
        :param output:  Output file path relative to workdir
        """
        out = os.path.join(self.workdir, output)
        tmpl = U.find_template(template, self.template_paths)

        if tmpl is None:
            raise RuntimeError(
                "Template not found in your search paths: " + template
            )

        content = T.template_compile(tmpl, self.pkgdata)
        open(out, "w").write(content)  # may throw IOError, OSError.

    def copyfiles(self):
        for o in self.files:
            dest = PU.to_srcdir(self.srcdir, o.install_path)
            o.copy(dest, self.force)

    def dumpfile(self):
        return os.path.join(self.workdir, "pmaker-filelist.pkl")

    def save(self, proto=pickle.HIGHEST_PROTOCOL):
        """
        Save file list (self.files).
        """
        pickle.dump(
            self.files,
            open(self.dumpfile(), "wb"),
            proto
        )

    def load(self):
        """
        Load the file list previously saved.

        It may throw IOError, OSError, etc.
        """
        files = pickle.load(open(self.dumpfile(), "rb"))

        if files:
            self.pkgdata.files = self.files = files

    def marker_path(self, step):
        return os.path.join(self.workdir, "pmaker-%(name)s.stamp" % step)

    def try_the_step(self, step):
        """
        Try to run given step.

        see also: pmaker.globals.PACKAGING_STEPS
        """
        marker = self.marker_path(step)

        if os.path.exists(marker):
            msg = "...The step looks already done"

            if self.force:
                logging.info("%s: %s" % (msg, step.name))
            else:
                logging.info("%s: Skip the step: %s" % (msg, step.name))
                return

        getattr(self, step.name, U.do_nothing)()
        self.shell("touch " + marker, timeout=10)

        if step.name == self.stepto:
            if step.name == STEP_BUILD:
                logging.info(
                    "Created packages in %(workdir)s: %(name)s" % self.pkgdata
                )
            sys.exit()

    def setup(self):
        U.createdir(self.workdir)
        U.createdir(self.srcdir)

        self.copyfiles()
        self.save()

    def preconfigure(self):
        if not self.files:
            self.load()

        for template, output in self._templates:
            self.genfile(template, output)

    def configure(self):
        pass

    def sbuild(self):
        pass

    def build(self):
        pass

    def run(self):
        """
        Run all of the processes to make a package: setup, configure, ...

        see also: pmaker.globals.PACKAGING_STEPS
        """
        for step in self._steps:
            logging.info(step.message % self.pkgdata)
            self.try_the_step(step)


# vim:sw=4 ts=4 et:
