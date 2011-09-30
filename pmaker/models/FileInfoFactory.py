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
from pmaker.globals import *  # TYPE_*, FILEINFOS
from pmaker.utils import checksum, st_mode_to_mode

import pmaker.models.FileInfo

import grp
import logging
import os
import os.path
import pwd
import stat



pmaker.models.FileInfo.init()  # Initialize FILEINFOS (fileinfos mapping table)



class FileInfoFactory(object):

    def _stat(self, path):
        """
        @path    str     Object's path (relative or absolute)
        @return  A tuple of (mode, uid, gid) or (None, None, None) if OSError was raised.
        """
        try:
            _stat = os.lstat(path)
        except OSError, e:
            logging.warn(e)
            return None

        return (_stat.st_mode, _stat.st_uid, _stat.st_gid)

    def _guess_ftype(self, st_mode):
        """
        @st_mode    st_mode
        """
        if stat.S_ISLNK(st_mode):
            ft = TYPE_SYMLINK

        elif stat.S_ISREG(st_mode):
            ft = TYPE_FILE

        elif stat.S_ISDIR(st_mode):
            ft = TYPE_DIR

        elif stat.S_ISCHR(st_mode) or stat.S_ISBLK(st_mode) \
            or stat.S_ISFIFO(st_mode) or stat.S_ISSOCK(st_mode):
            ft = TYPE_OTHER
        else:
            ft = TYPE_UNKNOWN  # Should not be reached

        return ft

    def create(self, path, create=False, filetype=TYPE_FILE, fileinfo_map=FILEINFOS, **kwargs):
        if create:
            _cls = fileinfo_map.get(filetype, False)
            assert _cls, "Could not get a class for filetype=" + filetype

            return _cls(path, create=True, **kwargs)
        else:
            return self.create_from_path(path, kwargs)

    def create_from_path(self, path, attrs=dict(), fileinfo_map=FILEINFOS, **kwargs):
        """
        Factory method. Creates and returns the *Info instance.

        @path   str   Object path (relative or absolute)
        @attrs  dict  Attributes set to FileInfo object result after creation
        """
        st = self._stat(path)

        attrs2 = dict(
            (k, v) for k, v in attrs.iteritems() \
                if k not in ("path", "mode", "uid", "gid", "checksum")
        )

        if st is None:
            return pmaker.models.FileInfo.UnknownInfo(path, **attrs)

        (st_mode, _uid, _gid) = st

        _filetype = self._guess_ftype(st_mode)

        if _filetype == TYPE_UNKNOWN:
            logging.warn(" Could not determine type for " + path)

        _checksum = _filetype == TYPE_FILE and checksum(path) or checksum()
        _mode = st_mode_to_mode(st_mode)

        _cls = fileinfo_map.get(_filetype, False)
        assert _cls, "Could not get a class for filetype=" + _filetype

        _mode = attrs.get("mode", _mode)
        _uid = attrs.get("uid", _uid)
        _gid = attrs.get("gid", _gid)
        _checksum = attrs.get("checksum", _checksum)

        fi = _cls(path, _mode, _uid, _gid, _checksum, **attrs2)

        return fi


# vim:sw=4 ts=4 expandtab:
