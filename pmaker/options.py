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
from pmaker.globals import PMAKER_VERSION
from pmaker.models.Bunch import Bunch

import pmaker.configurations as C
import pmaker.collectors.Collectors as Collectors
import pmaker.backend.registry as Backends
import pmaker.environ as E
import pmaker.parser as P

import logging
import optparse
import os.path
import sys


HELP_HEADER = """%prog [OPTION ...] [INPUT]

Arguments:

  INPUT   A file path or "-" (read data from stdin) to gather file paths.

          You can also specify "files" section in configuration files with
          -C/--config option.

          see pmaker(8) for more details.

Options:  see %prog --help

Examples:
  %prog -n foo files.list
  cat files.list | %prog -n foo -  # same as above.
  %prog -n foo -C config.json  # Specify files in JSON config also.

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


def parse_relations(relations):
    return P.parse(relations)


def setup_relations_option():
    """Relation option parameters.
    """
    def _cb(option, opt_str, value, parser):
        parser.values.relations = parse_relations(value)

    _help = """\
Semicolon (;) separated list of a pair of relation type and
targets separated with comma, separated with colon (:), e.g.
\"requires:curl,sed;obsoletes:foo-old\".

Expressions of relation types and targets are varied depends
on package format to use.
"""

    # TODO: callback interacts badly with configurations.
    return dict(action="callback", callback=_cb, type="string",
                default=[], help=_help)


def setup_template_path_option():
    def cb(option, opt_str, value, parser):
        if value not in parser.values.template_paths:
            parser.values.template_paths.append(value)

    return dict(action="callback", callback=cb, type="string",
                dest="template_paths", )


def get_content(path):
    content = ""
    try:
        content = open(path).read()

    except IOError:
        logging.warn(
            "Could not open %s to read content." % value
        )

    return content


def set_workdir(workdir, name, pversion):
    return os.path.join(os.path.abspath(workdir), "%s-%s" % (name, pversion))


class Options(Bunch):

    def __init__(self, **kwargs):
        """
        """
        self.env = E.Env()
        self.config = C.Config()
        self.oparser = optparse.OptionParser(HELP_HEADER,
                                             version=VERSION_STRING,
                                             )
        self.set_defaults()

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

    def __setup_rpm_options(self):
        rog = optparse.OptionGroup(self.oparser, "Rpm options")
        add_option = rog.add_option

        add_option("", "--dist",
            help="Build target distribution for mock [%default]"
        )
        add_option("", "--no-rpmdb", action="store_true",
            help="Do not refer rpm database to get metadata of files"
        )
        add_option("", "--no-mock", action="store_true",
            help="Build RPM with only using rpmbuild w/o mock" + \
                " (not recommended)"
        )

        self.oparser.add_option_group(rog)

    def make_default_summary(self, name):
        return "Custom package of " + name

    def missing_files(self, args):
        """
        Check if filelist is given already through config files or as
        rest of arguments.

        :param args: [listfile, ...] or []
        """
        return self.config.missing_files() and not args

    def parse_args(self, argv=sys.argv[1:]):
        (options, args) = self.oparser.parse_args(argv)

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

        try:
            loglevel = [
                logging.WARN, logging.INFO, logging.DEBUG
            ][options.verbosity]

        except IndexError:
            logging.warn("Bad Log level")
            loglevel = logging.WARN

        logging.getLogger().setLevel(loglevel)

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
