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
from pmaker.models.Bunch import Bunch
from pmaker.utils import singleton, memoize, parse_conf_value, \
    parse_list_str, unique

import ConfigParser as configparser
import glob
import logging
import os
import os.path
import sys

try:
    import yaml
except ImportError:
    logging.warn(" YAML module is not available. Disabled its support.")
    yaml = None

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        logging.warn(" JSON module is not available. Disabled its support.")
        json = None


def list_paths(basename, paths=None):
    if paths is None:
        home = os.environ.get("HOME", os.curdir)

        paths = ["/etc/%s.conf" % basename]
        paths += sorted(glob.glob("/etc/%s.d/*.conf" % basename))
        paths += [os.path.join(home, ".config", basename)]
        paths += [
            os.environ.get(
                "%sRC" % basename.upper(),
                os.path.join(home, ".%src" % basename)
            )
        ]
    else:
        assert isinstance(paths, list)

    return paths


class ConfigParser(object):

    def __init__(self, sep=","):
        pass


def configparser_load(paths, sep=","):
    config = Bunch()
    cparser = configparser.SafeConfigParser()

    for c in paths:
        if os.path.exists(c):
            logging.info("Loading config: " + c)

            try:
                cparser.read(c)

                for k, v in cparser.defaults().iteritems():
                    if sep in v:
                        config[k] = [
                            parse_conf_value(x) for x in parse_list_str(v)
                        ]
                    else:
                        config[k] = parse_conf_value(v)

                for s in cparser.sections():
                    for k in cparser.options(s):
                        v = cparser.get(s, k)
                        if sep in v:
                            config[k] = [
                                parse_conf_value(x) for x in parse_list_str(v)
                            ]
                        else:
                            config[k] = parse_conf_value(v)

            except Exception, e:
                logging.warn(e)

    return config


def configparser_load(paths, sep=","):
    config = Bunch()
    cparser = configparser.SafeConfigParser()

    for c in paths:
        if os.path.exists(c):
            logging.info("Loading config: " + c)

            try:
                cparser.read(c)

                for k, v in cparser.defaults().iteritems():
                    if sep in v:
                        config[k] = [
                            parse_conf_value(x) for x in parse_list_str(v)
                        ]
                    else:
                        config[k] = parse_conf_value(v)

                for s in cparser.sections():
                    for k in cparser.options(s):
                        v = cparser.get(s, k)
                        if sep in v:
                            config[k] = [
                                parse_conf_value(x) for x in parse_list_str(v)
                            ]
                        else:
                            config[k] = parse_conf_value(v)

            except Exception, e:
                logging.warn(e)

    return config


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
            workdir=workdir_defaults()["default"],
            upto=upto_defaults()["default"],
            format=get_package_format(),
            driver=driver_defaults()["default"],
            itype=itype_defaults()["default"],
            compressor=compressor_defaults()["default"],
            ignore_owner=False,
            force=False,

            config=None,

            verbosity=0,
            trace=False,

            destdir="",

            template_paths=tmpl_paths,

            name="",
            pversion="0.0.1",
            release="1",
            group="System Environment/Base",
            license="GPLv2+",
            url="http://localhost.localdomain",
            summary="",
            arch=False,
            relations=relations_defaults()["default"],
            packager=get_fullname(),
            email=get_email(),
            changelog="",

            dist="%s-%s-%s" % get_distribution(),

            no_rpmdb=False,
            no_mock=False,
        )

        return defaults

    def as_dict(self):
        return self._config


# vim:sw=4 ts=4 expandtab:
