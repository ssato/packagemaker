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
from pmaker.globals import PMAKER_RPMSPEC_VERSION

import pmaker.rpmspec.config as C
import pmaker.environ as E
import pmaker.models.Bunch as B
import pmaker.options as O
import pmaker.parser as P

import logging
import optparse
import os.path
import sys


HELP_HEADER = """%prog [OPTION ...] [PKG_NAME]

Arguments:

  PKG_NAME  Name represents package entity

Options:  see %prog --help

Examples:
  %prog foo
  %prog -t R R-foo
  %prog -t ghc-binlib bar
  %prog -t python baz
"""

VERSION_STRING = "%prog " + PMAKER_VERSION


setup_template_path_option = O.setup_template_path_option
set_workdir = O.set_workdir


class Options(B.Bunch):

    def __init__(self, **kwargs):
        """
        """
        self.env = E.Env()
        self.config = C.Config()
        self.oparser = optparse.OptionParser(HELP_HEADER,
                                             version=VERSION_STRING,
                                             )
        self.__setup_common_options()
        self.__setup_build_options()
        self.__setup_metadata_options()
        self.__setup_rpm_options()

    def get_defaults(self):
        return self.oparser.defaults

    def set_defaults(self, config=None, norc=True):
        """
        :param config:  Configuration file path :: str
        :param norc: No rc, i.e. do not load any default configs at all.
        """
        if config is None:
            if not norc:
                self.config.load_default_configs()
        else:
            self.config.load(config)

        self.oparser.set_defaults(**self.config)

    def __setup_common_options(self):
        """
        Setup common options.
        """
        add_option = self.oparser.add_option

        add_option("-C", "--config",
            help="Specify your custom configuration file which will be" + \
                " loaded *after* some default configuration files are loaded."
        )
        add_option("", "--norc", action="store_true",
            help="Do not load default configuration files"
        )
        add_option("", "--force", action="store_true",
            help="Force going steps even if the steps looks done already"
        )
        add_option("-v", "--verbose", action="count", dest="verbosity",
            help="Verbose mode")
        add_option("", "--debug", action="store_const", dest="verbosity",
            const=2, help="Debug mode (same as -vv)")
        add_option("", "--trace", action="store_true", help="Trace mode")
        add_option("-L", "--log", help="Log file [stdout]")

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
        add_option("-I", "--input-type", choices=choices, help=help)

        drivers = Backends.map()  # {backend_type: backend_class}
        choices = drivers.keys()
        help = "Packaging driver: %s [%%default]" % ", ".join(choices)
        add_option("", "--driver", choices=choices, help=help)
        add_option("", "--backend", dest="driver", choices=choices,
            help="Same as --driver option"
        )

        add_option("", "--destdir", help=DESTDIR_OPTION_HELP)
        add_option("-P", "--template-path", **setup_template_path_option())

        self.oparser.add_option_group(bog)

    def __setup_metadata_options(self):
        pog = optparse.OptionGroup(self.oparser, "Package metadata options")
        add_option = pog.add_option

        add_option("-n", "--name", help="Package name")  # Must be set
        add_option("", "--group",
            help="The group of the package [%default]. If your target" + \
                " format is RPM, take a look at" + \
                " /usr/share/doc/rpm-x.y.z/GROUPS."
        )
        add_option("", "--license",
            help="The license of the package [%default]"
        )
        add_option("", "--url", help="The url of the package [%default]")
        add_option("", "--summary", help="The summary of the package")

        choices = [ct.extension for ct in self.env.compressors]
        help = "Tool to compress src distribution archive: %s [%%default]" \
            % ", ".join(choices)
        add_option("-z", "--compressor", choices=choices, help=help)

        add_option("", "--arch", action="store_true",
            help="Set if this package is arch-dependent [false = noarch]"
        )
        add_option("", "--relations", **setup_relations_option())
        add_option("", "--packager", help="Packager's fullname [%default]")
        add_option("", "--email", help="Packager's email address [%default]")
        add_option("", "--pversion", help="Package's version [%default]")
        add_option("", "--release", help="Package's release [%default]")
        add_option("", "--ignore-owner", action="store_true",
            help="Force set owner and group of files to root"
        )
        add_option("", "--changelog",
            help="Specify text file contains changelog",
        )

        self.oparser.add_option_group(pog)

    def parse_args(self, argv=sys.argv[1:]):
        (options, args) = self.oparser.parse_args(argv)

        try:
            loglevel = [
                logging.WARN, logging.INFO, logging.DEBUG
            ][options.verbosity]

        except IndexError:
            logging.warn("Bad Log level")
            loglevel = logging.WARN

        logging.getLogger().setLevel(loglevel)

        if options.log:
            logging.getLogger().addHandler(logging.FileHandler(options.log))

        if not options.norc:
            self.set_defaults(norc=False)

            # retry parsing args with this configuration:
            (options, args) = self.oparser.parse_args(argv)

        if options.config is not None:
            self.set_defaults(options.config, norc=True)

            # Likewise:
            (options, args) = self.oparser.parse_args(argv)

            if not args:  # it means this config provides files also.
                options.input_type = "filelist.%s" % \
                    C.guess_type(options.config)

        if self.missing_files(args):
            logging.error(" Filelist was not given.\n")
            self.oparser.print_usage()

            sys.exit(-1)

        if options.name is None:
            options.name = raw_input("Package name: ")

        if options.summary is None:
            options.summary = self.make_default_summary(options.name)

        if options.changelog:
            options.changelog = get_content(options.changelog)

        options.workdir = set_workdir(
            options.workdir, options.name, options.pversion
        )

        return (options, args)


# vim:sw=4 ts=4 et:
