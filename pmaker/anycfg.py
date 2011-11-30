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

import pmaker.parser as P
import pmaker.utils as U

import ConfigParser as configparser
import glob
import logging
import os
import os.path
import sys


try:
    import yaml
except ImportError:
    logging.warn("YAML module is not available. Disabled its support.")
    yaml = None

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        logging.warn("JSON module is not available. Disabled its support.")
        json = None


try:
    # First, try lxml compatible with elementtree and looks faster a lot.
    # see also: http://diveintopython3-ja.rdy.jp/xml.html:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        try:
            import elementtree.ElementTree as etree
        except ImportError:
            logging.warn(
                "ElementTree module is not available. Disabled XML support."
            )
            etree = None


CONFIG_EXTS = [INI_EXTS, JSON_EXTS, YAML_EXTS, XML_EXTS, ] = [
    ("ini", ), ("json", "jsn"), ("yaml", "yml"), ("xml", ),
]
EXT2CLASS_MAP = dict()

CTYPES = [CTYPE_INI, CTYPE_JSON, CTYPE_YAML, CTYPE_XML] = [
    "ini", "json", "yaml", "xml",
]
CTYPE2CLASS_MAP = dict()


def list_paths(basename, paths=None, ext="conf"):
    """
    :param basename: Application's basic name, e.g. pmaker.
    :param paths: Configuration path list.
    :param ext: Extension of configuration files.
    """
    if paths is None:
        home = os.environ.get("HOME", os.curdir)

        paths = []

        if basename is not None:
            paths += ["/etc/%s.%s" % (basename, ext)]
            paths += sorted(glob.glob("/etc/%s.d/*.%s" % (basename, ext)))
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

    def load(self, path_, sep=",", **kwargs):
        if not os.path.exists(path_):
            logging.info("%s does not exist." % path_)
            return

        logging.info("Loading config: " + path_)
        config = Bunch()

        try:
            self._parser.read(path_)

            # Treat key and value pairs in [DEFAULTS] as special.
            for k, v in self._parser.defaults().iteritems():
                if sep in v:
                    config[k] = [
                        P.parse(x) for x in U.parse_list_str(v)
                    ]
                else:
                    config[k] = P.parse(v)

            for s in self._parser.sections():
                config[s] = Bunch()

                for k in self._parser.options(s):
                    v = self._parser.get(s, k)
                    if sep in v:
                        config[s][k] = [
                            P.parse(x) for x in U.parse_list_str(v)
                        ]
                    else:
                        config[s][k] = P.parse(v)

        except Exception, e:
            logging.warn(e)

        return config


EXT2CLASS_MAP[INI_EXTS] = IniConfigParser
CTYPE2CLASS_MAP[CTYPE_INI] = IniConfigParser


def dict_to_bunch(json_obj_dict):
    return Bunch(**json_obj_dict)


class JsonConfigPaser(IniConfigParser):

    def load(self, path_, *args, **kwargs):
        if json is None:
            logging.warn("JSON is not a supported configuration format.")
            return Bunch()
        else:
            return json.load(open(path_), object_hook=dict_to_bunch)


EXT2CLASS_MAP[JSON_EXTS] = JsonConfigPaser
CTYPE2CLASS_MAP[CTYPE_JSON] = JsonConfigPaser


if yaml is not None:

    # @see http://bit.ly/pxKVqS
    class YamlBunchLoader(yaml.Loader):

        def __init__(self, *args, **kwargs):
            yaml.Loader.__init__(self, *args, **kwargs)

            self.add_constructor(
                u"tag:yaml.org,2002:map",
                type(self).construct_yaml_map
            )

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
                    "expected a mapping node, but found %s" % node.id,
                    node.start_mark
                )

            mapping = Bunch()

            for key_node, value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    hash(key)
                except TypeError, exc:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        "found unacceptable key (%s)" % exc,
                        key_node.start_mark
                    )
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


EXT2CLASS_MAP[YAML_EXTS] = YamlConfigPaser
CTYPE2CLASS_MAP[CTYPE_YAML] = YamlConfigPaser


def etree_to_Bunch(root):
    """
    Convert XML ElementTree to a collection of Bunch objects.
    """
    tree = Bunch()

    if len(root):  # It has children.
        # FIXME: Configuration item cannot have both attributes and
        # values (list) at the same time in current implementation:
        tree[root.tag] = [etree_to_Bunch(c) for c in root]
    else:
        tree[root.tag] = Bunch(**root.attrib)

    return tree


class XmlConfigParser(IniConfigParser):

    def load(self, path_, *args, **kwargs):
        if etree is None:
            logging.warn("XML is not a supported configuration format.")
            return Bunch()
        else:
            tree = etree.parse(path_)
            root = tree.getroot()

            return etree_to_Bunch(root)


# TODO: It's experimental yet.
#EXT2CLASS_MAP[XML_EXTS] = XmlConfigPaser
#CTYPE2CLASS_MAP[CTYPE_XML] = XmlConfigPaser


def guess_class(conf, default=IniConfigParser):
    """
    :param conf: Configuration file path
    """
    cls = default
    fn_ext = os.path.splitext(conf)

    if len(fn_ext) > 1:
        ext = fn_ext[1].lower()[1:]  # strip '.' at the head.

        for exts in EXT2CLASS_MAP.keys():
            if ext in exts:
                cls = EXT2CLASS_MAP[exts]

    return cls


class AnyConfigParser(object):

    def __init__(self, forced_type=None):
        """
        :param forced_type: Force set configuration parser class' type.
        """
        self.forced_class = CTYPE2CLASS_MAP.get(forced_type, None)

    def load(self, conf, forced_type=None, **kwargs):
        """
        :param conf:  Path to configuration file.
        """
        if forced_type is not None:
            cls = CTYPE2CLASS_MAP[forced_type]  # may throw KeyError
        elif self.forced_class is not None:
            cls = self.forced_class
        else:
            cls = guess_class(conf)

        logging.info("Using config parser: " + str(cls))
        parser = cls()

        return parser.load(conf, **kwargs)

    def loads(self, name, paths=None):
        if paths is None:
            paths = list_paths(name)

        config = Bunch()

        for p in paths:
            c = self.load(p)
            config.update(c)

        return config


# vim:sw=4 ts=4 et:
