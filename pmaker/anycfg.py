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
from pmaker.environ import Env
from pmaker.models.Bunch import Bunch
from pmaker.parser import parse

import ConfigParser as configparser
import glob
import logging
import os
import os.path
import sys


"""Uncomment the followings if it's used standalone (w/ pmaker.parser):

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
"""

# ... and comment this:
json = Env().json
yaml = Env().yaml


def list_paths(basename=None, paths=None):
    if paths is None:
        home = os.environ.get("HOME", os.curdir)

        paths = []

        if basename is not None:
            paths += ["/etc/%s.conf" % basename]
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


class IniConfigParser(object):

    def __init__(self):
        self._parser = configparser.SafeConfigParser()
        self.config = Bunch()

    def load(self, path_, sep=",", **kwargs):
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

    def loads(self, name=None, paths=[]):
        if not paths:
            paths = list_paths(name)

        for p in paths:
            c = self.load(p)
            self.config.update(c)


def dict_to_bunch(json_obj_dict):
    return Bunch(**json_obj_dict)


class JsonConfigPaser(IniConfigParser):

    def load(self, path_, *args, **kwargs):
        if json is None:
            logging.warn("JSON is not a supported configuration format.")
            return Bunch()
        else:
            return json.load(open(path_), object_hook=dict_to_bunch)


# @see http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
class YamlBunchLoader(yaml.Loader):

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = Bunch()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)

        mapping = Bunch()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value

        return mapping


class YamlConfigPaser(IniConfigParser):

    def load(self, path_, *args, **kwargs):
        if yaml is None:
            logging.warn("YAML is not a supported configuration format.")
            return Bunch()
        else:
            return yaml.load(open(path_), Loader=YamlBunchLoader)


class AnyConfigParser(IniConfigParser):

    def load(self, conf, **kwargs):
        """
        :param conf:  Path to configuration file.
        """
        fn_ext = os.path.splitext(conf)
        parser = IniConfigParser()

        if len(fn_ext) > 1:
            ext = fn_ext[1].lower()

            if ext in ("json", "jsn"):
                parser = JsonConfigPaser()
            elif ext in ("yaml", "yml"):
                parser = YamlConfigPaser()

        return parser.load(conf, **kwargs)


# vim:sw=4 ts=4 et:
