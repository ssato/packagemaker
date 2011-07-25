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
from pmaker.utils import *
from pmaker.collectors.Filters import *
from pmaker.collectors.Modifiers import *
from pmaker.collectors.RpmModifiers import *
from pmaker.models.FileInfo import *
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.models.RpmFileInfoFactory import RpmFileInfoFactory

import glob
import logging
import os
import os.path
import sys


if JSON_ENABLED:
    import json
else:
    class json:
        @staticmethod
        def load(*args):
            return ()



class Collector(object):
    """Abstract class for collector classes
    """

    _enabled = True
    _type = None

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def type(cls):
        return cls._type

    @classmethod
    def enabled(cls):
        return cls._enabled

    def collect(self, *args, **kwargs):
        if not self.enabled():
            raise RuntimeError("Disabled because required function is not available: " + self.__name__)

    def get_modifiers(self):
        """
        Returns registered modifiers sorted by these priorities.
        """
        for m in sorted(self.modifiers):
            yield m



class FilelistCollector(Collector):
    """
    Collector to collect fileinfo list from files list in simple format:

    Format: A file or dir path (absolute or relative) |
            Comment line starts with "#" |
            Glob pattern to list multiple files or dirs
    """

    _type = "filelist"

    def __init__(self, filelist, options):
        """
        @filelist  str  file to list files and dirs to collect or "-"
                        (files and dirs list will be read from stdin)
        @options   optparse.Values
        """
        self.filelist = filelist

        # TBD:
        #self.trace = options.trace
        self.trace = False

        self.filters = [UnsupportedTypesFilter(), ReadAccessFilter()]
        self.modifiers = [AttributeModifier()]

        if options.destdir:
            self.modifiers.append(DestdirModifier(options.destdir))

        if options.ignore_owner:
            self.modifiers.append(OwnerModifier(0, 0))  # 0 == root's uid and gid

        if options.format == PKG_FORMAT_RPM:
            self.fi_factory = RpmFileInfoFactory()

            self.modifiers.append(RpmAttributeModifier())

            if not options.no_rpmdb:
                self.modifiers.append(RpmConflictsModifier(options.name))
        else:
            self.fi_factory = FileInfoFactory()

    @staticmethod
    def open(path):
        return path == "-" and sys.stdin or open(path)

    @staticmethod
    def parse_line(line):
        """
        Parse str and returns a dict to create a FileInfo instance.

        >>> cls = FilelistCollector
        >>> rref = dict(install_path="/var/lib/network/resolv.conf", uid=0, gid=0)
        >>> (ps, r) = cls.parse_line("/etc/resolv.conf,install_path=/var/lib/network/resolv.conf,uid=0,gid=0")
        >>> assert ps == ["/etc/resolv.conf"]
        >>> assert dicts_comp(r, rref)
        """
        ss = parse_list_str(line, ",")

        p = ss[0]
        paths = "*" in p and glob.glob(p) or [p]

        avs = (av for av in (parse_list_str(kv, "=") for kv in ss[1:]) if av)
        attrs = dict((a, parse_conf_value(v)) for a, v in avs)
        if "*" in p:
            attrs["create"] = False

        return (paths, attrs)

    @classmethod
    def _parse(cls, line):
        """Parse the line and returns FileInfo list generator.
        """
        line = line.rstrip().strip() # remove extra white spaces at the top and the end.

        if not line or line.startswith("#"):
            return []
        else:
            (paths, attrs) = cls.parse_line(line)
            return [FileInfo(path, **attrs) for path in paths]

    def list_fileinfos(self, listfile):
        """Read paths from given file line by line and returns path list sorted by
        dir names. There some speical parsing rules for the file list:

        * Empty lines or lines start with "#" are ignored.
        * The lines contain "*" (glob match) will be expanded to real dir or file
          names: ex. "/etc/httpd/conf/*" will be
          ["/etc/httpd/conf/httpd.conf", "/etc/httpd/conf/magic", ...] .

        @listfile  str  Path list file name or "-" (read list from stdin)
        """
        return unique(concat(self._parse(l) for l in self.open(listfile).readlines()))

    def _collect(self, listfile):
        """Collect FileInfo objects from given path list.

        @listfile  str  File, dir and symlink paths list
        """
        for fi in self.list_fileinfos(listfile):
            if not fi.create:
                fi = self.fi_factory.create(fi.path)

            # filter out if any filter(fi) -> True
            filtered = any(filter(fi) for filter in self.filters)

            if not filtered:
                fi.conflicts = dict()

                # Too verbose but useful in some cases:
                if self.trace:
                    logging.debug(" fi=%s" % str(fi))

                for modifier in self.get_modifiers():
                    fi = modifier.update(fi)

                yield fi

    def collect(self):
        return [fi for fi in self._collect(self.filelist)]



class JsonFilelistCollector(FilelistCollector):
    """
    Collector for files list in JSON format such as:

    {
        ...
        "files": [
            {
                "path": "/a/b/c",
                "attrs" : {
                    "create": 0,
                    "install_path": "/a/c",
                    "uid": 100,
                    "gid": 0,
                    "rpmattr": "%config(noreplace)",
                    ...
                }
            },
            ...
        ]
    }
    """
    global JSON_ENABLED

    _enabled = JSON_ENABLED
    _type = "filelist.json"

    @classmethod
    def _parse(cls, params):
        path = params.get("path", False)

        if not path or path.startswith("#"):
            return []
        else:
            paths = "*" in path and glob.glob(path) or [path]
            attrs = params.get("attrs", dict())

            return (FileInfo(path, **attrs) for path in paths)

    def list_fileinfos(self, listfile):
        data = json.load(self.open(listfile))
        return unique(concat(self._parse(d) for d in data["files"]))



def init(collectors_map=COLLECTORS):
    for cls in (FilelistCollector, JsonFilelistCollector):
        if cls.enabled():
            collectors_map[cls.type()] = cls


# vim: set sw=4 ts=4 expandtab:
