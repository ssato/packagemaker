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
from pmaker.globals import PKG_FORMAT_RPM
from pmaker.models.Bunch import Bunch

import pmaker.collectors.Filters as F
import pmaker.collectors.Modifiers as M
import pmaker.collectors.RpmModifiers as RM
import pmaker.models.FileObjectFactory as Factory

import pmaker.configurations as C
import pmaker.environ as E
import pmaker.parser as P
import pmaker.utils as U

import glob
import logging
import os
import os.path
import sys


class Collector(object):

    _types = []

    @classmethod
    def types(cls):
        return cls._types

    def get_modifiers(self):
        """
        self.modifiers are objects willl modify fileobjs.
        """
        for m in sorted(self.modifiers):
            yield m


def driver_to_format(driver):
    """
    >>> driver_to_format("autotools.single.rpm")
    'rpm'
    """
    return P.parse_list(driver, ".")[-1]


def lopen(path):
    return path == "-" and sys.stdin or open(path)


class FilelistCollector(Collector):
    """
    Class to collect fileobj list from path list in simple format:

    Each line consists of a file or dir path (absolute or relative) and
    optional attribute specifiers follows just after "," (a comma), or comment
    line starts with "#", or glob pattern to list multiple files or dirs.
    """

    _types = ["filelist", "filelist.plain"]

    def __init__(self, listfile, config, **kwargs):
        """
        :param listfile: File path to list path of objects or "-" (these will
                         be read from stdin. :: str
        :param config: Objects holding configuration parameters
        """
        self.listfile = listfile
        self.config = config

        # TBD:
        self.trace = False

        self.filters = [F.UnsupportedTypesFilter(), F.ReadAccessFilter()]
        self.modifiers = [M.AttributeModifier()]

        if config.destdir:
            self.modifiers.append(M.DestdirModifier(config.destdir))

        if config.ignore_owner:
            self.modifiers.append(M.OwnerModifier())  # uid = gid = 0

        self.use_rpmdb = not config.no_rpmdb

        if driver_to_format(config.driver) == PKG_FORMAT_RPM:
            self.modifiers.append(RM.RpmAttributeModifier())

            if self.use_rpmdb:
                self.modifiers.append(RM.RpmConflictsModifier(config.name))

    def _parse(self, line):
        """Parse the line and returns FileInfo list generator.
        """
        # remove extra white spaces at the top and the end.
        line = line.rstrip().strip()

        if not line or line.startswith("#"):
            return []
        else:
            (paths, attrs) = P.parse_line_of_filelist(line)

            return [Factory.create(p, self.use_rpmdb, **attrs) for p in paths]

    def list(self, listfile):
        """
        Read paths from given file line by line and returns path list sorted by
        dir names. There some speical parsing rules for the file list:

        * Empty lines or lines start with "#" are ignored.
        * The lines contain "*" (glob match) will be expanded to real dir or
          file names: ex. "/etc/httpd/conf/*" will be
          ["/etc/httpd/conf/httpd.conf", "/etc/httpd/conf/magic", ...] .

        :param listfile: Path list file name or "-" (read list from stdin)
        """
        return U.unique(
            U.concat(self._parse(l) for l in lopen(listfile).readlines() if l)
        )

    def _collect(self, listfile):
        """Collect FileObject instances from given path list.

        :param listfile: See the above description.
        """
        for fo in self.list(listfile):
            # filter out if any filter(fi) -> True
            filtered = any(filter(fo) for filter in self.filters)

            if filtered:
                logging.debug(" filter out: path=" + fo.path)
            else:
                for modifier in self.get_modifiers():
                    fo = modifier.update(fo)

                # Too verbose but useful in some cases:
                if self.trace:
                    logging.debug(" (result) fo: path=" + fo.path)

                yield fo

    def collect(self):
        return [f for f in self._collect(self.listfile) if f]


class AnyFilelistCollector(FilelistCollector):
    """
    File path list loader for any formats pmaker.anycfg can support.
    Formats of input files are detected automatically.
    """

    _types = ["filelist.any"] + ["filelist." + ct for ct in C.TYPES]

    def __init__(self, listfile, config, itype=None, **kwargs):
        """
        :param itype:  Input file type, e.g. "json", "yaml".
        """
        super(AnyFilelistCollector, self).__init__(listfile, config, **kwargs)

        self.itype = None

        if itype is not None:
            if itype in C.TYPES:
                self.itype = itype
            else:
                logging.warn("Invalid type passed: " + itype)

    def _parse(self, bobj):
        """
        :param bobj: A Bunch object holds path and attrs (metadata) of files.
        """
        path = bobj.get("path", False)

        if not path or path.startswith("#"):
            return []
        else:
            paths = "*" in path and glob.glob(path) or [path]
            attrs = bobj.get("attrs", dict())

            return [Factory.create(p, self.use_rpmdb, **attrs) for p in paths]

    def list(self, listfile):
        cfg = C.Config()
        data = cfg.load(listfile, self.itype)

        if not getattr(data, "files", False):
            raise RuntimeError(
                "'files' not defined in given filelist: " + listfile
            )

        return unique(concat(self._parse(o) for o in data.files))


def map():
    collectors = (FilelistCollector, AnyFilelistCollector)
    return dict(U.concat([(t, c) for t in c.types()] for c in collectors))


def default():
    return FilelistCollector.types()[0]


# vim:sw=4 ts=4 et:
