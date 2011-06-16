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

import grp
import logging
import os
import os.path
import pwd
import stat


try:
    import xattr  # pyxattr

except ImportError:
    # Make up a "Null-Object" like class mimics xattr module.
    class xattr(object):
        def get_all(self, *args):
            return ()




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
            return (None, None, None)

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

    def create(self, path, attrs=None, fileinfo_maps=FILEINFOS):
        """Factory method. Create and return the *Info instance.

        @path   str   Object path (relative or absolute)
        @attrs  dict  Attributes set to FileInfo object result after creation
        """
        st = self._stat(path)

        if st is None:
            return UnknownInfo(path)

        (_mode, _uid, _gid) = st

        xs = xattr.get_all(path)
        _xattrs = (xs and dict(xs) or {})

        _filetype = self._guess_ftype(_mode)

        if _filetype == TYPE_UNKNOWN:
            logging.info(" Could not get the result: %s" % path)

        if _filetype == TYPE_FILE:
            _checksum = checksum(path)
        else:
            _checksum = checksum()

        _cls = fileinfo_maps.get(_filetype, False)
        assert _cls, "Should not reached here! filetype=%s" % _filetype

        fi = _cls(path, _mode, _uid, _gid, _checksum, _xattrs)

        if attrs:
            for attr, val in attrs.iteritems():
                setattr(fi, attr, val)

        return fi


# vim: set sw=4 ts=4 expandtab:
