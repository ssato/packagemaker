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
from pmaker.utils import parse_conf_value

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



NULL_DICT = dict()



def parse_template_list_str(templates):
    """
    simple parser for options.templates.

    >>> assert parse_template_list_str("") == {}
    >>> assert parse_template_list_str("a:b") == {"a": "b"}
    >>> assert parse_template_list_str("a:b,c:d") == {"a": "b", "c": "d"}
    """
    if templates:
        return dict(kv.split(":") for kv in templates.split(","))
    else:
        return dict()


def relations_parser(relations_str):
    """
    >>> relations_parser("requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old")
    [('requires', ['bash', 'zsh']), ('obsoletes', ['sysdata']), ('conflicts', ['sysdata-old'])]
    """
    if not relations_str:
        return []

    rels = [rel.split(":") for rel in relations_str.split(";")]
    return [(reltype, reltargets.split(",")) for reltype, reltargets in rels]



def option_parser(config):
    """
    Command line option parser.
    """
    p = optparse.OptionParser("""%prog [OPTION ...] FILE_LIST

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

  It loads opitonal parameters from multiple configuration files if there are
  in order of /etc/pmaker.conf, /etc/pmaker.d/*.conf, ~/.config/pmaker, any
  path set in the environment variable PMAKERRC and ~/.pmakerrc.

Examples:
  %prog -n foo files.list
  cat files.list | %prog -n foo -  # same as above.

  %prog -n foo --pversion 0.2 -l MIT files.list
  %prog -n foo --relations "requires:httpd,/sbin/service;obsoletes:foo-old" files.list
""",
    version = "%prog " + __version__
    )

    config.load_defaults()
    defaults = config.as_dict()

    p.set_defaults(**defaults)

    bog = optparse.OptionGroup(p, "Build options")
    bog.add_option("-w", "--workdir", help="Working dir to dump outputs [%default]")
    bog.add_option("", "--upto", type="choice", choices=upto_params["choices"],
        help="Which packaging step you want to proceed to: " + upto_params["choices_str"] + " [Default: %default]")
    bog.add_option("", "--driver", type="choice", choices=pdriver, help=pdriver_help)
    bog.add_option("", "--format", type="choice", choices=pformats, help=pformats_help)
    bog.add_option("", "--itype", type="choice", choices=itypes, help=itypes_help)
    bog.add_option("", "--destdir", help="Destdir (prefix) you want to strip from installed path [%default]. "
        "For example, if the target path is \"/builddir/dest/usr/share/data/foo/a.dat\", "
        "and you want to strip \"/builddir/dest\" from the path when packaging \"a.dat\" and "
        "make it installed as \"/usr/share/foo/a.dat\" with the package , you can accomplish "
        "that by this option: \"--destdir=/builddir/destdir\"")
    bog.add_option("", "--templates", help="Use custom template files. "
        "TEMPLATES is a comma separated list of template output and file after the form of "
        "RELATIVE_OUTPUT_PATH_IN_SRCDIR:TEMPLATE_FILE such like \"package.spec:/tmp/foo.spec.tmpl\", "
        "and \"debian/rules:mydebrules.tmpl, Makefile.am:/etc/foo/mymakefileam.tmpl\". "
        "Supported template syntax is Python Cheetah: http://www.cheetahtemplate.org .")
    bog.add_option("", "--link", action="store_true", help="Make symlinks for symlinks instead of copying them")
    bog.add_option("", "--with-pyxattr", action="store_true", help="Get/set xattributes of files with pure python code.")
    p.add_option_group(bog)

    pog = optparse.OptionGroup(p, "Package metadata options")
    pog.add_option("-n", "--name", help="Package name [%default]")
    pog.add_option("", "--group", help="The group of the package [%default]")
    pog.add_option("", "--license", help="The license of the package [%default]")
    pog.add_option("", "--url", help="The url of the package [%default]")
    pog.add_option("", "--summary", help="The summary of the package")
    pog.add_option("-z", "--compressor", type="choice", choices=compressor_choices,
        help="Tool to compress src archives [%default]")
    pog.add_option("", "--arch", action="store_true", help="Make package arch-dependent [false - noarch]")
    pog.add_option("", "--relations",
        help="Semicolon (;) separated list of a pair of relation type and targets "
        "separated with comma, separated with colon (:), "
        "e.g. \"requires:curl,sed;obsoletes:foo-old\". "
        "Expressions of relation types and targets are varied depends on "
        "package format to use")
    pog.add_option("", "--packager", help="Specify packager's name [%default]")
    pog.add_option("", "--mail", help="Specify packager's mail address [%default]")
    pog.add_option("", "--pversion", help="Specify the package version [%default]")
    pog.add_option("", "--ignore-owner", action="store_true", help="Ignore owner and group of files and then treat as root's")
    pog.add_option("", "--changelog", help="Specify text file contains changelog")
    p.add_option_group(pog)

    rog = optparse.OptionGroup(p, "Options for rpm")
    rog.add_option("", "--dist", help="Target distribution (for mock) [%default]")
    rog.add_option("", "--no-rpmdb", action="store_true", help="Do not refer rpm db to get extra information of target files")
    rog.add_option("", "--no-mock", action="store_true", help="Build RPM with only using rpmbuild (not recommended)")
    rog.add_option("", "--scriptlets", help="Specify the file contains rpm scriptlets")
    p.add_option_group(rog)

    sog = optparse.OptionGroup(p, "Self-build options")
    sog.add_option("", "--release-build", action="store_true", help="Make a release build")
    sog.add_option("", "--include-plugins", help="Comma separated list of plugin files to be included in dist.")
    p.add_option_group(sog)

    tog = optparse.OptionGroup(p, "Test options")
    tog.add_option("", "--tests", action="store_true", help="Run tests.")
    tog.add_option("", "--tlevel", type="choice", choices=test_choices,
        help="Select the level of tests to run. Choices are " + ", ".join(test_choices) + " [%default]")
    tog.add_option("", "--profile", action="store_true", help="Enable profiling")
    p.add_option_group(tog)

    p.add_option("", "--force", action="store_true", help="Force going steps even if the steps looks done")
    p.add_option("-v", "--verbose", action="store_true", help="Verbose mode")
    p.add_option("-q", "--quiet", action="store_true", help="Quiet mode")
    p.add_option("-D", "--debug", action="store_true", help="Debug mode")

    p.add_option("", "--build-self", action="store_true", help="Package itself (self-build)")
    p.add_option("", "--show-examples", action="store_true", help="Show examples")
    p.add_option("", "--dump-rc", action="store_true", help="Show conf file example")

    return p



class Config(object):
    """Object to get/set configuration values.
    """

    def __init__(self, prog="pmaker", profile=None, paths=None,
            defaults=NULL_DICT):
        """
        @param  prog      Program name
        @param  profile   Profile name will be used for config selection
        @param  paths     Configuration file path list
        @param  defaults  Default configuration values
        """
        self._prog = prog
        self._profile = profile
        self._paths = self._list_paths(prog, paths)
        self._config = defaults

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
            return NULL_DICT

        if profile is None:
            return cparser.defaults()
        else:
            return dict((k, parse_conf_value(v)) for k, v in cparser.items(profile))

    def load(self, path=None):
        paths = path is None and self._paths or [path]
        self._config = self._load(paths, self._profile) 

    def load_defaults(self, bsteps=BUILD_STEPS, upto=UPTO, itypes=COLLECTORS,
            pmakers=PACKAGE_MAKERS, compressors=COMPRESSORS):
        """
        Load default configurations.
        """
        upto_params = dict(
            choices = [name for name, _logmsg, _helptxt in bsteps],
            choices_s = ", ".join("%s (%s)" % (name, helptxt) for name, _logmsg, helptxt in bsteps),
            default = upto,
        )

        drivers = unique(t[0] for t in pmakers.keys())
        drivers_help = "Packaging driver's type: %s [%%default]" % ", ".join(pmakers)

        pformats = unique(t[1] for t in pmakers.keys())
        pformats_help = "Packaging format: %s [%%default]" % ", ".join(pformats)

        itypes = sorted(itypes.keys())
        itypes_help = "Input type: %s [%%default]" % ", ".join(itypes)

        # TODO: Detect appropriate distribution (for mock) automatically.
        (dist_name, dist_version) = get_distribution()
        dist = "%s-%s" % (dist_name, dist_version)

        compressor = get_compressor(compressors)  # cmd, extension, am_option,
        compressor_choices = [ext for _c, ext, _a in compressors]

        defaults = dict(
            workdir = os.path.join(os.getcwd(), "workdir"),
            upto = upto_params["default"],
            format = dist_name == "debian" and "deb" or "rpm",
            itype = "filelist",
            compressor = compressor[1],
            ignore_owner = False,
            force = False,

            verbose = False,
            quiet = False,
            debug = False,

            destdir = "",

            #link = False,
            #with_pyxattr = False,

            name = "",
            pversion = "0.1",
            group = "System Environment/Base",
            license = "GPLv2+",
            url = "http://localhost.localdomain",
            summary = "",
            arch = False,
            relations = "",
            packager = get_fullname(),
            email = get_email(),
            changelog = "",

            dist = dist,

            no_rpmdb = False,
            no_mock = False,
            scriptlets = "",
        )

        self._config = defaults

    def as_dict(self):
        return self._config



# vim: set sw=4 ts=4 expandtab:
