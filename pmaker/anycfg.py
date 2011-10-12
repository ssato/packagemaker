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
from pmaker.parser import parse

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


class IniParser(object):

    def __init__(self, basename):
        self._parser = configparser.SafeConfigParser()
        self._basename = basename
        self.config = Bunch()

    def load(self, path_, sep=","):
        if not os.path.exists(path_):
            logging.warn("%s does not exist. Do nothing." % path_)
            return

        logging.info("Loading config: " + path_)
        config = Bunch()

        try:
            self._parser.read(path_)

            for k, v in self._parser.defaults().iteritems():
                config.defaults = Bunch()

                if sep in v:
                    config.defaults[k] = [
                        parse(x) for x in parse_list_str(v)
                    ]
                else:
                    config.defaults[k] = parse(v)

            for s in self._parser.sections():
                config[s] = Bunch()

                for k in self._parser.options(s):
                    v = self._parser.get(s, k)
                    if sep in v:
                        config[s][k] = [
                            parse(x) for x in parse_list_str(v)
                        ]
                    else:
                        config[s][k] = parse(v)

        except Exception, e:
            logging.warn(e)

        return config

    def loads(self, paths=[]):
        if not paths:
            paths = list_paths(self._basename)

        for p in paths:
            c = self.load(p)
            self.config.update(c)


class YamlConfigPaser(IniParser):

    def load(self, path_, sep=","):
        if yaml is None:
            return yaml.load(open(path_))
        else:
            logging.warn("YAML is not a supported configuration format.")
            return Bunch()


class JsonConfigPaser(IniParser):

    def load(self, path_, sep=","):
        if json is None:
            return json.load(open(path_))
        else:
            logging.warn("JSON is not a supported configuration format.")
            return Bunch()


# vim:sw=4 ts=4 et:
