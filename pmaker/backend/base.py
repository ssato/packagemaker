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
from pmaker.globals import BUILD_STEPS, STEP_BUILD
from pmaker.models.Bunch import Bunch

import pmaker.utils as U
import pmaker.shell as S

import cPickle as pickle
import logging
import os.path
import sys


class Base(object):
    """
    Abstract class for children to implement packaging backends.
    """
    global BUILD_STEPS

    _format = None  # packaging format, e.g. rpm, deb.
    _strategy = None  # packaging strategy, e.g. autotools.single.

    _steps = BUILD_STEPS  # packaging (build) steps to run.

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
        # e.g. ("autotools.single/configure.ac": "configure.ac"),
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

    def __setup_aliases(self, package):
        self.objects = package.objects

        self.workdir = package.workdir
        self.destdir = package.destdir
        self.srcdir = package.srcdir

        self.upto = package.upto

    def __init__(self, package, **kwargs):
        """
        :param package:  Object holding all data and metadata for packaging
        """
        self.package = package

        self.__setup_aliases(package)
        #self.package.relations = self.relations_maps(package.relations)

        for k, v in kwargs.iteritems():
            if getattr(self, k, None) is None:
                setattr(self, k, v)

    def shell(self, cmd_s, workdir=None, **kwargs):
        """
        Run shell command.
        """
        if workdir is None:
            workdir = self.package.workdir

        return S.run(cmd_s, workdir=workdir, **kwargs)

    def genfile(self, template, output):
        """
        Generate file in workdir from given template.

        :param template:  Template file path relative to search dirs
        :param output:  Output file path relative to workdir
        """
        out = os.path.join(self.workdir, output)
        tmpl = U.find_template(template, self.package.template_paths)

        if tmpl is None:
            raise RuntimeError(
                "Template not found in your search paths: " + template
            )

        content = U.compile_template(tmpl, self.package)
        open(out, "w").write(content)  # may throw IOError, OSError.

    def copyfiles(self):
        for o in self.package.objects:
            dest = to_srcdir(self.srcdir, o.install_path)
            o.copy(dest, self.package.force)

    def dumpfile(self):
        return os.path.join(self.package.workdir, "pmaker-filelist.pkl")

    def save(self, proto=pickle.HIGHEST_PROTOCOL):
        """
        Save file list (package.objects).
        """
        pickle.dump(
            self.package.objects,
            open(self.dumpfile(), "wb"),
            proto
        )

    def load(self):
        """
        Load the file list previously saved.

        It may throw IOError, OSError, etc.
        """
        objects = pickle.load(open(self.dumpfile(), "rb"))

        if objects:
            self.package.objects = self.objects = objects

    def marker_path(self, step):
        return os.path.join(self.workdir, "pmaker-%s.stamp" % step)

    def try_the_step(self, step):
        """
        Try to run given step.
        """
        if os.path.exists(self.marker_path(step)):
            msg = "...The step looks already done"

            if self.package.force:
                logging.info("%s: %s" % (msg, step))
            else:
                logging.info("%s: Skip the step: %s" % (msg, step))
                return

        getattr(self, step, U.do_nothing)()
        self.shell("touch " + self.marker_path(step), timeout=10)

        if step == self.package.upto:
            if step == STEP_BUILD:
                logging.info(
                    "Created packages in %(workdir)s: %(name)s" % self.package
                )
            sys.exit()

    def setup(self):
        U.createdir(self.workdir)
        U.createdir(self.srcdir)

        self.copyfiles()
        self.save()

    def preconfigure(self):
        if not self.package.objects:
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
        """
        d = dict(workdir=self.package.workdir, pname=self.package.name)

        for step, msgfmt, _helptxt in self._steps:
            logging.info(msgfmt % d)
            self.try_the_step(step)


# vim:sw=4 ts=4 et:
