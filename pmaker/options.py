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
from pmaker.globals import PMAKER_NAME, PMAKER_VERSION
from pmaker.utils import singleton
from pmaker.parser import parse

import pmaker.collectors.Collectors as Collectors
import pmaker.backend.registry as Backends
import pmaker.environ as E

import logging
import optparse
import os
import os.path
import sys


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

VERSION_STRING = "%prog " + PMAKER_VERSION

DESTDIR_OPTION_HELP = """\
Destdir (prefix) to strip from installation path.

For example, if the path is \"/builddir/dest/etc/foo/a.dat\"
and \"/builddir/dest\" to be stripped from the path when
packaging \"a.dat\", and it needs to be installed as
\"/etc/foo/a.dat\" with that package, you can accomplish
this by this option: \"--destdir=/builddir/destdir\".
"""


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
class Options(Bunch):

    def __init__(self, defaults=None, env=None, **kwargs):
        """
        :param defaults: Defalut values :: Bunch
        :param env: Env instance :: Env
        """
        self.env = env is None and E.Env() or env

        if defaults is None:
            defaults = self._defaults(self.env)

        self.oparser = optparse.OptionParser(HELP_HEADER,
                                             version=VERSION_STRING,
                                             )
        self.oparser.set_defaults(**defaults)

        self.__setup_common_options()
        self.__setup_build_options()
        self.__setup_metadata_options()
        self.__setup_rpm_options()

    def __defaults(self, env):
        """
        """
        defaults = Bunch()

        defaults.config = None
        defaults.force = False
        defaults.verbosity = 0  # verbose and debug option.

        # build options:
        defaults.workdir = env.workdir
        defaults.stepto = env.upto
        defaults.input_type = Collectors.default()  # e.g. "filelist.json"
        defaults.driver = Backends.default()  # e.g. "autotools.single.rpm"
        defaults.destdir = ""
        defaults.template_paths = env.template_paths

        # package metadata options:
        defaults.name = None
        defaults.group = "System Environment/Base"
        defaults.license = "GPLv3+"
        defaults.url = "http://localhost.localdomain"
        defaults.summary = None
        defaults.compressor = env.compressor.extension  # extension
        defaults.arch = False
        defaults.relations = ""
        defaults.packager = env.fullname
        defaults.email = env.email
        defaults.pversion = "0.0.1"
        defaults.release = "1"
        defaults.ignore_owner = False
        defaults.changelog = None

        # rpm options:
        defaults.dist = env.dist.label
        defaults.no_rpmdb = False
        defaults.no_mock = False

        return defaults

    def __setup_common_options(self):
        """
        Setup common options.
        """
        add_option = self.oparser.add_option

        add_option("-C", "--config", help="Configuration file path")
        add_option("", "--force", action="store_true",
            help="Force going steps even if the steps looks done")
        add_option("-v", "--verbose", action="count", dest="verbosity",
            help="Verbose mode")
        add_option("", "--debug", action="store_const", dest="verbosity",
            const=2, help="Debug mode (same as -vv)")
        add_option("", "--trace", action="store_true", help="Trace mode")

    def __setup_build_options(self):
        global PACKAGING_STEPS, DESTDIR_OPTION_HELP

        bog = optparse.OptionGroup(self.oparser, "Build options")
        add_option = bog.add_option

        add_option("-w", "--workdir",
            help="Specify working dir to output results [%default]"
        )

        choices = [step.name for step in self.env.steps]
        help = "Target step you want to go to: %s [%%default]" % choices
        add_option("", "--stepto", choices=choices, help=help)
        add_option("", "--upto", dest="stepto", choices=choices,
            help="Same as --stepto option (kept for backward compatibility)."
        )

        collectors = Collectors.map()  # {collector_type: collector_class}
        choices = collectors.keys()
        help = "Input type: %s [%%default]" % ", ".join(choices)
        add_option("", "--input-type", choices=choices, help=help)

        ## Deprecated (substituted with --driver/--backend option):
        #choices = self.env.formats
        #help = "Package format: %s [%%default]" % ", ".join(choices)
        #add_option("", "--format", choices=choices, help=help)

        drivers = Backends.map()  # {backend_type: backend_class}
        choices = drivers.keys()
        help = "Packaging driver: %s [%%default]" % ", ".join(choices)
        add_option("", "--driver", choices=choices, help=help)
        add_option("", "--backend", dest="driver", choices=choices,
            help="Same as --driver option"
        )

        add_option("", "--destdir", help=DESTDIR_OPTION_HELP)

        add_option("-P", "--template-path", action="append",
            dest="template_paths"
        )

        self.oparser.add_option_group(bog)

    def __setup_metadata_options(self):
        pog = optparse.OptionGroup(self.oparser, "Package metadata options")
        add_option = pog.add_option

        add_option("-n", "--name", help="Package name")  # Must not be None
        add_option("", "--group", help="The group of the package [%default]")
        add_option("", "--license",
            help="The license of the package [%default]"
        )
        add_option("", "--url", help="The url of the package [%default]")
        add_option("", "--summary", help="The summary of the package")

        choices = [ct.extension for ct in self.env.compressors]
        help = "Tool to compress the src distribution archive: %s [%default]" \
            % ", ".join(choices)
        add_option("-z", "--compressor", choices=choices, help=help)

        add_option("", "--arch", action="store_true",
            help="Make package arch-dependent [false = noarch]"
        )

        add_option("", "--relations", **setup_relations_option())

        add_option("", "--packager", help="Packager's fullname [%default]")
        add_option("", "--email", help="Packager's email address [%default]")
        add_option("", "--pversion", help="Package's version [%default]")
        add_option("", "--release", help="Package's release [%default]")
        add_option("", "--ignore-owner", action="store_true",
            help="Force set owner and group of targets to root"
        )
        add_option("", "--changelog",
            help="Specify text file contains changelog"
        )

        self.oparser.add_option_group(pog)

    def __setup_rpm_options(self):
        rog = optparse.OptionGroup(self.oparser, "Rpm options")
        add_option = rog.add_option

        add_option("", "--dist",
            help="Build target distribution for mock [%default]"
        )
        add_option("", "--no-rpmdb", action="store_true",
            help="Do not refer rpm database to get metadata of objects"
        )
        rog.add_option("", "--no-mock", action="store_true",
            help="Build RPM with only using rpmbuild (not recommended)"
        )

        self.oparser.add_option_group(rog)

    def parse_args(self, argv):
        (options, args) = self.oparser.parse_args(argv)

        if options.name is None:
            options.name = raw_input("Package's name: ")

        if options.summary is None:
            options.summary = "Custom package " + options.name

        return (options, args)


# vim:sw=4 ts=4 et:
