#
# Copyright (C) 2011 Satoru SATOH <ssato @ redhat.com>
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
from pmaker.models.Bunch import Bunch
from pmaker.anycfg import AnyConfigParser
from pmaker.environ import Env
from pmaker.globals import PMAKER_NAME, PMAKER_VERSION, \
    BUILD_STEPS, COLLECTORS
from pmaker.utils import singleton, unique
from pmaker.parser import parse

from pmaker.collectors.Collectors import FilelistCollector, \
    init as init_collectors
from pmaker.makers.PackageMaker import init as init_packagemaker
from pmaker.makers.RpmPackageMaker import init as init_rpmpackagemaker
from pmaker.makers.DebPackageMaker import init as init_debpackagemaker

import logging
import optparse
import os
import os.path
import sys


# Initialize some global hash tables: COLLECTORS, PACKAGE_MAKERS
init_collectors()
init_packagemaker()
init_rpmpackagemaker()
init_debpackagemaker()


HELP_HEADER = """%prog [OPTION ...] INPUT

Arguments:

  INPUT   A file path or "-" (read data from stdin) to gather file paths.

          Various format such as JSON is supported but most basic and simplest
          format is like the followings:

          - Lines are consist of aboslute path of target file/dir/symlink
          - The lines starting with "#" in the list file are ignored
          - "*" in paths are intepreted as glob matching pattern;

          ex. if there were files 'c', 'd' and 'e' in the dir and the path
              '/a/b/*' was given, it's just same as '/a/b/c', '/a/b/d' and
              '/a/b/e' were given.

Configuration files:

  Pmaker loads parameter configurations from multiple configuration files if
  there are in order of /etc/pmaker.conf, /etc/pmaker.d/*.conf,
  ~/.config/pmaker, any path set in the environment variable PMAKERRC and
  ~/.pmakerrc.

Examples:
  %prog -n foo files.list
  cat files.list | %prog -n foo -  # same as above.

  %prog -n foo --pversion 0.2 --license MIT files.list
  %prog -n foo --relations "requires:httpd,/bin/tar;obsoletes:bar" files.list
"""

HELP_VERSION = "%prog " + PMAKER_VERSION


DESTDIR_OPTION_HELP = """\
Destdir (prefix) to strip from installation path [%default]. 

For example, if the path is \"/builddir/dest/etc/foo/a.dat\"
and \"/builddir/dest\" to be stripped from the path when
packaging \"a.dat\", and it needs to be installed as
\"/etc/foo/a.dat\" with that package, you can accomplish
this by this option: \"--destdir=/builddir/destdir\".
"""


class Defaults(Bunch):

    def __init__(self, env=Env()):
        self.workdir = env.workdir
        self.upto = env.upto
        self.format = env.format
        self.compressor = env.compressor.triple
        self.ignore_owner = False
        self.force = False

        self.backend = env.driver
        self.driver = env.driver
        self.frontend = env.itype
        self.itype = env.itype

        self.config = None

        self.verbosity = 0
        self.trace = False

        self.destdir = ""

        self.template_paths = tmpl_paths

        self.name = ""
        self.pversion = "0.0.1"
        self.release = "1"
        self.group = "System Environment/Base"
        self.license = "GPLv2+"
        self.url = "http://localhost.localdomain"
        self.summary = ""
        self.arch = False
        self.relations = env.relations
        self.packager = env.fullname
        self.email = env.email
        self.changelog = ""

        self.dist = "%s-%s-%s" % env.dist

        self.no_rpmdb = False
        self.no_mock = False


def setup_relations_option():
    """Relation option parameters.
    """
    def cb(option, opt_str, value, parser):
        parser.values.relations = parse(value)

    _help = """\
Semicolon (;) separated list of a pair of relation type and
targets separated with comma, separated with colon (:), e.g.
\"requires:curl,sed;obsoletes:foo-old\".

Expressions of relation types and targets are varied depends
on package format to use.
"""

    return dict(action="callback", callback=cb, type="string",
                default="", help=_help)


def set_workdir(workdir, name, pversion):
    return os.path.join(os.path.abspath(workdir), "%s-%s" % (name, pversion))


@singleton
class Config(Bunch):

    def __init__(self, app, defaults=None, **kwargs):
        self.oparser = optparse.OptionParser(HELP_HEADER,
                                             version=HELP_VERSION,
                                             )
        if defaults is None:
            defaults = Defaults()

        self.oparser.set_defaults(**defaults)

        self.env = Env()

        self.add_global_options()
        self.add_build_options()
        self.add_metadata_options()
        self.add_rpm_options()

    def add_option(self, *args, **kwargs):
        self.oparser.add_option(*args, **kwargs)

    def add_global_options(self):
        """
        Setup global (common/basic) options.
        """
        self.add_option("-C", "--config", help="Configuration file path")
        self.add_option("", "--force", action="store_true",
            help="Force going steps even if the steps looks done")
        self.add_option("-v", "--verbose", action="count", dest="verbosity",
            help="Verbose mode")
        self.add_option("", "--debug", action="store_const", dest="verbosity",
            const=2, help="Debug mode (same as -vv)")
        self.add_option("", "--trace", action="store_true", help="Trace mode")

    def add_build_options(self):
        """
        Setup build options.
        """
        global BUILD_STEPS, DESTDIR_OPTION_HELP

        bog = optparse.OptionGroup(self.oparser, "Build options")
        bog.add_option("-w", "--workdir",
            help="Working dir to dump outputs [%default]")

        choices = [n for n, _l, _h in BUILD_STEPS]
        help = "Packaging step to proceed to: %s [%%default]" % choices
        bog.add_option("", "--upto", choices=choices, help=help)

        choices = self.env.formats
        help = "Package format: %s [%%default]" % ", ".join(choices)
        bog.add_option("", "--format", choices=choices, help=help)

        #choices = self.env.backends
        choices = ["autotools.single"]
        help = "Packaging backend: %s [%%default]" % ", ".join(choices)
        bog.add_option("", "--backend",  choices=choices, help=help)

        choices = self.env.frontends.keys()
        help = "Input type: %s [%%default]" % ", ".join(choices)
        bog.add_option("", "--frontend", choices=choices, help=help)

        choices = [e for _c, e, _a in self.env.compressor.triple]
        help = "Tool to compress src distribution archive: %s [%default]" \
            % ", ".join(choices)
        bog.add_option("-z", "--compressor", choices=choices, help=help)

        bog.add_option("", "--destdir", help=DESTDIR_OPTION_HELP)

        bog.add_option("-P", "--template-path", action="append",
            dest="template_paths")

        self.oparser.add_option_group(bog)

    def add_metadata_options(self):
        """
        Setup package metadata options.
        """
        pog = optparse.OptionGroup(self.oparser, "Package metadata options")

        pog.add_option("-n", "--name", help="Package name [%default]")
        pog.add_option("", "--group", help="The group of the package [%default]")
        pog.add_option("", "--license",
            help="The license of the package [%default]")
        pog.add_option("", "--url", help="The url of the package [%default]")
        pog.add_option("", "--summary", help="The summary of the package")
        pog.add_option("", "--arch", action="store_true",
            help="Make package arch-dependent [false = noarch]")
        pog.add_option("", "--relations", **setup_relations_option()),
        pog.add_option("", "--packager",
            help="Specify packager's name [%default]")
        pog.add_option("", "--email",
            help="Specify packager's mail address [%default]")
        pog.add_option("", "--pversion",
            help="Specify the package's version [%default]")
        pog.add_option("", "--release",
            help="Specify the package's release [%default]")
        pog.add_option("", "--ignore-owner", action="store_true",
            help="Force set owner and group of targets to root")
        pog.add_option("", "--changelog",
            help="Specify text file contains changelog")
        self.oparser.add_option_group(pog)

    def add_rpm_options(self):
        """
        Setup package metadata options.
        """
        rog = optparse.OptionGroup(self.oparser, "Options for rpm")
        rog.add_option("", "--dist",
            help="Target distribution for mock [%default]")
        rog.add_option("", "--no-rpmdb", action="store_true",
            help="Do not refer rpm database to get metadata of targets")
        rog.add_option("", "--no-mock", action="store_true",
            help="Build RPM with only using rpmbuild (not recommended)")
        self.oparser.add_option_group(rog)

    def parse_args(self, argv):
        (options, args) = self.oparser.parse_args(argv)

        return (options, args)


# vim:sw=4 ts=4 et:
