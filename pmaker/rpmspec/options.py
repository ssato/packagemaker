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
from pmaker.rpmspec.globals import PMAKER_RPMSPEC_VERSION

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

  PKG_NAME  Name represents the target package

Options:  see %prog --help

Examples:
  %prog foo
  %prog -t R R-foo
  %prog -t ghc-binlib bar
  %prog -t python baz
"""

VERSION_STRING = "%prog " + PMAKER_RPMSPEC_VERSION


setup_template_path_option = O.setup_template_path_option


def set_workdir(workdir, name):
    """
    >>> workdir = "/tmp/w"
    >>> assert set_workdir(workdir, "foo") == "/tmp/w/foo-build"
    >>> workdir = "/tmp/w/foo-build"
    >>> assert set_workdir(workdir, "foo") == workdir
    """
    subdir = name + "-build"

    if workdir.endswith(subdir):
        return os.path.abspath(workdir)
    else:
        return os.path.join(os.path.abspath(workdir), subdir)


class Options(B.Bunch):

    def __init__(self, **kwargs):
        self.env = E.Env()
        self.config = C.Config()
        self.oparser = optparse.OptionParser(HELP_HEADER,
                                             version=VERSION_STRING,
                                             )
        self.__setup_common_options()
        self.__setup_build_options()
        self.__setup_metadata_options()

    def __setup_common_options(self):
        add_option = self.oparser.add_option

        add_option("-v", "--verbose", action="count", dest="verbosity",
            help="Verbose mode")
        add_option("", "--debug", action="store_const", dest="verbosity",
            const=2, help="Debug mode (same as -vv)")
        add_option("-L", "--log", help="Log file [stdout]")

    def __setup_build_options(self):
        bog = optparse.OptionGroup(self.oparser, "Build options")
        add_option = bog.add_option

        add_option("-w", "--workdir",
            help="Specify working dir to output results [%default]"
        )
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
        add_option("", "--url", help="The url of the package [%default]")
        add_option("", "--summary", help="The summary of the package")

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

        if options.name is None:
            options.name = raw_input("Package name: ")

        options.workdir = set_workdir(
            options.workdir, options.name, options.pversion
        )

        return (options, args)


# vim:sw=4:ts=4:et:
