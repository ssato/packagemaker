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
import doctest
import glob
import logging
import os
import os.path
import sys

try:
    from collections import OrderedDict as dict

except ImportError:
    pass



NULL_DICT = dict()



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


# vim: set sw=4 ts=4 expandtab:
