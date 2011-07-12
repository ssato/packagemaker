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
from pmaker.environ import *
from pmaker.utils import parse_conf_value, memoize
from pmaker.collectors.Collectors import FilelistCollector, init as init_collectors
from pmaker.makers.PackageMaker import init as init_packagemaker
from pmaker.makers.RpmPackageMaker import init as init_rpmpackagemaker
from pmaker.makers.DebPackageMaker import init as init_debpackagemaker

import ConfigParser as configparser
import glob
import logging
import optparse
import os
import os.path
import sys

try:
    from collections import OrderedDict as dict
except ImportError:
    pass


# Initialize some global hash tables: COLLECTORS, PACKAGE_MAKERS
init_collectors()
init_packagemaker()
init_rpmpackagemaker()
init_debpackagemaker()


HELP_HEADER = """%prog [OPTION ...] FILE_LIST

Arguments:

  FILE_LIST  a file contains file paths list or "-" (read paths list from
             stdin).

             Various format such as JSON data is supported but most basic
             and simplest format is like the followings:

             - Lines are consist of aboslute path of target file/dir/symlink
             - The lines starting with "#" in the list file are ignored
             - "*" in paths are intepreted as glob matching pattern;

               ex. if there were files 'c', 'd' and 'e' in the dir and the
                   path '/a/b/*' was given, it's just same as
                   '/a/b/c', '/a/b/d' and '/a/b/e' were given.

Configuration files:

  It loads parameter configurations from multiple configuration files if there
  are in order of /etc/pmaker.conf, /etc/pmaker.d/*.conf, ~/.config/pmaker, any
  path set in the environment variable PMAKERRC and ~/.pmakerrc.

Examples:
  %prog -n foo files.list
  cat files.list | %prog -n foo -  # same as above.

  %prog -n foo --pversion 0.2 --license MIT files.list
  %prog -n foo --relations "requires:httpd,/sbin/service;obsoletes:foo-old" files.list
"""


def parse_list_str(optstr, sep=","):
    """
    simple parser for optstr gives a list of items separated with "," (comma).

    >>> assert parse_list_str("") == []
    >>> assert parse_list_str("a,b") == ["a", "b"]
    >>> assert parse_list_str("a,b,") == ["a", "b"]
    """
    return [p for p in optstr.split(sep) if p]


def parse_relations(optstr):
    """
    Returns list of (relation_type, relation_targets).

    >>> parse_relations("requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old")
    [('requires', ['bash', 'zsh']), ('obsoletes', ['sysdata']), ('conflicts', ['sysdata-old'])]
    """
    def type_and_targets(optstr):
        for rel in parse_list_str(optstr, ";"):
            if ":" not in rel or rel.endswith(":"):
                continue

            (_type, _targets) = parse_list_str(rel, ":")
            _targets = parse_list_str(_targets, ",")

            if _targets:
                yield (_type, _targets)

    return [(t, ts) for t, ts in type_and_targets(optstr)]


# FIXME: Ugly
def upto_defaults(upto=UPTO, build_steps=BUILD_STEPS):
    choices = [name for name, _l, _h in build_steps]
    help = "Packaging step you want to proceed to: %s [%%default]" % \
        ", ".join("%s (%s)" % (name, help) for name, _l, help in build_steps)
    default = upto

    return dict(choices=choices, help=help, default=default)


def format_defaults(formats=PKG_FORMATS):
    choices = formats
    help = "Package format: %s [%%default]" % ", ".join(choices)
    default = get_package_format()

    return dict(choices=choices, help=help, default=default)


def driver_defaults(pmakers=PACKAGE_MAKERS):
    choices = unique(pmakers.keys())
    help = "Packaging driver: %s [%%default]" % ", ".join(choices)
    default = "autotools." + get_package_format()

    return dict(choices=choices, help=help, default=default)


def itype_defaults(itypes=COLLECTORS):
    """
    @param  itypes  Map of Input data type such as "filelist", "filelist.json"
                    and Collector classes.
    """
    choices = itypes.keys()
    help = "Input type: %s [%%default]" % ", ".join(itypes)
    default = FilelistCollector.type()

    return dict(choices=choices, help=help, default=default)


def compressor_defaults(compressors=COMPRESSORS):
    """
    @param  compressors  list of (cmd, extension, am_option) of compressor.
    """
    compressor = get_compressor(compressors)  # cmd, extension, am_option,

    choices = [ext for _c, ext, _a in compressors]
    help = "Tool to compress src archive when building src distribution [%default]"
    default = compressor[1]  # extension

    return dict(choices=choices, help=help, default=default)


def relations_defaults():
    """Relation option parameters.
    """
    def cb(option, opt_str, value, parser):
        parser.values.relations = parse_relations(value)

    _help = """Semicolon (;) separated list of a pair of relation type and
targets separated with comma, separated with colon (:), e.g.
\"requires:curl,sed;obsoletes:foo-old\".  Expressions of relation types and
targets are varied depends on package format to use"""

    return dict(action="callback", callback=cb, type="string",
                default="", help=_help)


def workdir_defaults():
    """Relation option parameters.
    """
    def cb(option, opt_str, value, parser):
        name = parser.values.name
        version = parser.values.pversion
        workdir = os.path.join(value, "%s-%s" % (name, version))

        parser.values.workdir = os.path.abspath(workdir)

    _help="Working dir to dump outputs [%default]"
    _default = os.path.join(os.getcwd(), "workdir")

    return dict(action="callback", callback=cb, type="string",
        default=_default, help=_help)


def parse_args(argv=sys.argv[1:], defaults=None, upto=UPTO,
        build_steps=BUILD_STEPS, formats=PKG_FORMATS, drivers=PACKAGE_MAKERS,
        itypes=COLLECTORS, tmpl_search_paths=TEMPLATE_SEARCH_PATHS):
    """
    Parse command line options and args

    @return  (parser, options, args)
    """
    if defaults is None:
        defaults = Config.defaults()

    p = optparse.OptionParser(HELP_HEADER, version = "%prog " + PMAKER_VERSION)
    p.set_defaults(**defaults)

    p.add_option("-C", "--config", help="Configuration file path", default=None)

    bog = optparse.OptionGroup(p, "Build options")
    bog.add_option("-w", "--workdir", **workdir_defaults())

    bog.add_option("", "--upto", type="choice", **upto_defaults(upto, build_steps))
    bog.add_option("", "--format", type="choice", **format_defaults(formats))
    bog.add_option("", "--driver", type="choice", **driver_defaults(drivers))
    bog.add_option("", "--itype", type="choice", **itype_defaults(itypes))

    bog.add_option("", "--destdir", help="Destdir (prefix) you want to strip from installed path [%default]. "
        "For example, if the target path is \"/builddir/dest/usr/share/data/foo/a.dat\", "
        "and you want to strip \"/builddir/dest\" from the path when packaging \"a.dat\" and "
        "make it installed as \"/usr/share/foo/a.dat\" with the package , you can accomplish "
        "that by this option: \"--destdir=/builddir/destdir\"")

    bog.add_option("-P", "--template-path", action="append", dest="template_paths", default=tmpl_search_paths)

    #bog.add_option("", "--templates", help="Use custom template files. "
    #    "TEMPLATES is a comma separated list of template output and file after the form of "
    #    "RELATIVE_OUTPUT_PATH_IN_SRCDIR:TEMPLATE_FILE such like \"package.spec:/tmp/foo.spec.tmpl\", "
    #    "and \"debian/rules:mydebrules.tmpl, Makefile.am:/etc/foo/mymakefileam.tmpl\". "
    #    "Supported template syntax is Python Cheetah: http://www.cheetahtemplate.org .")

    #bog.add_option("", "--link", action="store_true", help="Make symlinks for symlinks instead of copying them")
    #bog.add_option("", "--with-pyxattr", action="store_true", help="Get/set xattributes of files with pure python code.")
    p.add_option_group(bog)

    pog = optparse.OptionGroup(p, "Package metadata options")
    pog.add_option("-n", "--name", help="Package name [%default]")
    pog.add_option("", "--group", help="The group of the package [%default]")
    pog.add_option("", "--license", help="The license of the package [%default]")
    pog.add_option("", "--url", help="The url of the package [%default]")
    pog.add_option("", "--summary", help="The summary of the package")
    pog.add_option("-z", "--compressor", type="choice", **compressor_defaults())
    pog.add_option("", "--arch", action="store_true", help="Make package arch-dependent [false = noarch]")
    pog.add_option("", "--relations", **relations_defaults()),
    pog.add_option("", "--packager", help="Specify packager's name [%default]")
    pog.add_option("", "--email", help="Specify packager's mail address [%default]")
    pog.add_option("", "--pversion", help="Specify the package's version [%default]")
    pog.add_option("", "--release", help="Specify the package's release [%default]")
    pog.add_option("", "--ignore-owner", action="store_true",
        help="Ignore owner and group of files and then treat as root's")
    pog.add_option("", "--changelog", help="Specify text file contains changelog")
    p.add_option_group(pog)

    rog = optparse.OptionGroup(p, "Options for rpm")
    rog.add_option("", "--dist", help="Target distribution (for mock) [%default]")
    rog.add_option("", "--no-rpmdb", action="store_true", help="Do not refer rpm db to get extra information of target files")
    rog.add_option("", "--no-mock", action="store_true", help="Build RPM with only using rpmbuild (not recommended)")
    p.add_option_group(rog)

    p.add_option("", "--force", action="store_true", help="Force going steps even if the steps looks done")

    p.add_option("-v", "--verbose", action="count", dest='verbosity', help="Verbose mode")
    p.add_option("", "--debug", action='store_const', dest='verbosity', const=2, help="Debug mode (same as -vv)")

    (options, args) = p.parse_args(argv)

    return (p, options, args)



class Config(object):
    """Object to get/set configuration values.
    """

    def __init__(self, prog="pmaker", profile=None, paths=None):
        """
        @param  prog      Program name
        @param  profile   Profile name will be used for config selection
        @param  paths     Configuration file path list
        @param  defaults  Default configuration values
        """
        self._prog = prog
        self._profile = profile
        self._paths = self._list_paths(prog, paths)
        self._config = self.defaults()

    @classmethod
    def _list_paths(cls, prog, paths=None):
        if paths is None:
            home = os.environ.get("HOME", os.curdir)

            paths = ["/etc/%s.conf" % prog]
            paths += sorted(glob.glob("/etc/%s.d/*.conf" % prog))
            paths += [os.path.join(home, ".config", prog)]
            paths += [os.environ.get("%sRC" % prog.upper(), os.path.join(home, ".%src" % prog))]
        else:
            assert isinstance(paths, list)

        return paths

    @classmethod
    def _load(cls, paths, profile=None):
        cparser = configparser.SafeConfigParser()
        loaded = False

        for c in paths:
            if os.path.exists(c):
                logging.info("Loading config: " + c)

                try:
                    cparser.read(c)
                    loaded = True

                except Exception, e:
                    logging.warn(e)

        if not loaded:
            return dict() 

        if profile is None:
            return cparser.defaults()
        else:
            return dict((k, parse_conf_value(v)) for k, v in cparser.items(profile))

    def load(self, path=None):
        paths = path is None and self._paths or [path]
        delta = self._load(paths, self._profile) 
        self._config.update(delta)

    @classmethod
    def defaults(cls, bsteps=BUILD_STEPS, upto=UPTO, itypes=COLLECTORS,
            pmakers=PACKAGE_MAKERS, compressors=COMPRESSORS,
            tmpl_paths=TEMPLATE_SEARCH_PATHS):
        """
        Load default configurations.
        """
        defaults = dict(
            workdir = workdir_defaults()["default"],
            upto = upto_defaults()["default"],
            format = get_package_format(),
            driver = driver_defaults()["default"],
            itype = itype_defaults()["default"],
            compressor = compressor_defaults()["default"],
            ignore_owner = False,
            force = False,

            verbosity = 0,

            destdir = "",

            template_paths = tmpl_paths,

            #link = False,
            #with_pyxattr = False,

            name = "",
            pversion = "0.1",
            release = "1",
            group = "System Environment/Base",
            license = "GPLv2+",
            url = "http://localhost.localdomain",
            summary = "",
            arch = False,
            relations = relations_defaults()["default"],
            packager = get_fullname(),
            email = get_email(),
            changelog = "",

            dist = "%s-%s-%s" % get_distribution(),

            no_rpmdb = False,
            no_mock = False,
        )

        return defaults

    def as_dict(self):
        return self._config



# vim: set sw=4 ts=4 expandtab:
