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
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.models.RpmFileInfoFactory import RpmFileInfoFactory
from pmaker.models.Target import Target

import glob
import logging
import os
import os.path
import sys


try:
    import json
    JSON_ENABLED = True

except ImportError:
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
    def register(cls, cmaps=COLLECTORS):
        if cls.enabled():
            cmaps[cls.type()] = cls

    @classmethod
    def enabled(cls):
        return cls._enabled

    def collect(self, *args, **kwargs):
        if not self.enabled():
            raise RuntimeError("Pluing %s cannot run as necessary function is not available." % self.__name__)

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

    def __init__(self, filelist, pkgname, options):
        """
        @filelist  str  file to list files and dirs to collect or "-"
                        (read files and dirs list from stdin)
        @pkgname   str  package name to build
        @options   optparse.Values
        """
        super(FilelistCollector, self).__init__(filelist, options)

        self.filelist = filelist

        # TBD:
        #self.trace = options.trace
        self.trace = False

        self.filters = [UnsupportedTypesFilterr()]
        self.modifiers = []

        if options.destdir:
            self.modifiers.append(DestdirModifier(options.destdir))

        if options.ignore_owner:
            self.modifiers.append(OwnerModifier(0, 0))  # 0 == root's uid and gid

        if options.format == "rpm":
            self.fi_factory = RpmFileInfoFactory()

            self.modifiers.append(RpmAttributeModifier())

            if not options.no_rpmdb:
                self.modifiers.append(RpmConflictsModifier(pkgname))
        else:
            self.fi_factory = FileInfoFactory()

    @staticmethod
    def open(path):
        return path == "-" and sys.stdin or open(path)

    @classmethod
    def _parse(cls, line):
        """Parse the line and returns Target (path) list.
        """
        if not line or line.startswith("#"):
            return []
        else:
            return [Target(p) for p in glob.glob(line.rstrip())]

    def list_targets(self, listfile):
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
        for target in self.list_targets(listfile):
            fi = self.fi_factory.create(target.path)
            fi.conflicts = {}
            fi.target = fi.path

            # Too verbose but useful in some cases:
            if self.trace:
                logging.debug(" fi=%s" % str(fi))

            for filter in self.filters:
                if filter.pred(fi):  # filter out if pred -> True:
                    continue

            for modifier in self.get_modifiers():
                fi = modifier.update(fi, target, self.trace)

            yield fi

    def collect(self):
        ## Is it needed?
        #return unique(fi for fi in self._collect(self.filelist))
        return [fi for fi in self._collect(self.filelist)]



class ExtFilelistCollector(FilelistCollector):
    """
    Collector to collect fileinfo list from files list in simple format:

    Format: A file or dir path (absolute or relative) |
            Comment line starts with "#" |
            Glob pattern to list multiple files or dirs
    """
    _enabled = True
    _type = "filelist.ext"

    def __init__(self, filelist, pkgname, options):
        super(ExtFilelistCollector, self).__init__(filelist, pkgname, options)
        self.modifiers.append(TargetAttributeModifier())

    @staticmethod
    def parse_line(line):
        """
        >>> cls = ExtFilelistCollector
        >>> cls.parse_line("/etc/resolv.conf,target=/var/lib/network/resolv.conf,uid=0,gid=0\\n")
        ('/etc/resolv.conf', [('target', '/var/lib/network/resolv.conf'), ('uid', 0), ('gid', 0)])
        """
        path_attrs = line.rstrip().split(",")
        path = path_attrs[0]
        attrs = []

        for attr, val in (kv.split("=") for kv in path_attrs[1:]):
            attrs.append((attr, parse_conf_value(val)))   # e.g. "uid=0" -> ("uid", 0), etc.

        return (path, attrs)

    @classmethod
    def _parse(cls, line):
        """Parse the line and returns Target (path) list.

        TODO: support glob expression in path.

        >>> cls = ExtFilelistCollector
        >>> cls._parse("#\\n")
        []
        >>> cls._parse("")
        []
        >>> cls._parse(" ")
        []
        >>> t = Target("/etc/resolv.conf", {"target": "/var/lib/network/resolv.conf", "uid": 0, "gid": 0})
        >>> ts = cls._parse("/etc/resolv.conf,target=/var/lib/network/resolv.conf,uid=0,gid=0\\n")
        >>> assert [t] == ts, str(ts)
        """
        if not line or line.startswith("#") or " " in line:
            return []
        else:
            (path, attrs) = cls.parse_line(line)
            return [Target(path, dict(attrs)) for path, attrs in zip(glob.glob(path), [attrs])]



class JsonFilelistCollector(FilelistCollector):
    """
    Collector for files list in JSON format such as:

    [
        {
            "path": "/a/b/c",
            "target": {
                "target": "/a/c",
                "uid": 100,
                "gid": 0,
                "rpmattr": "%config(noreplace)",
                ...
            }
        },
        ...
    ]
    """
    global JSON_ENABLED

    _enabled = JSON_ENABLED
    _type = "filelist.json"

    def __init__(self, filelist, pkgname, options):
        super(JsonFilelistCollector, self).__init__(filelist, pkgname, options)
        self.modifiers.append(TargetAttributeModifier())

    @classmethod
    def _parse(cls, path_dict):
        path = path_dict.get("path", False)

        if not path or path.startswith("#"):
            return []
        else:
            return [Target(p, path_dict["target"]) for p in glob.glob(path)]

    def list_targets(self, listfile):
        return unique(concat(self._parse(d) for d in json.load(self.open(listfile))))



def init():
    FilelistCollector.register()
    ExtFilelistCollector.register()
    JsonFilelistCollector.register()

# vim: set sw=4 ts=4 expandtab:
