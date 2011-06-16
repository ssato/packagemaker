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
#
from pmaker.globals import *
from pmaker.utils import *
from pmaker.models.FileOperations import *

import logging
import os.path



class FileInfo(object):
    """The class of which objects to hold meta data of regular files, dirs and
    symlinks. This is for regular file and the super class for other types.
    """

    operations = FileOperations
    filetype = TYPE_FILE
    is_copyable = True

    def __init__(self, path, mode, uid, gid, checksum, xattrs, **kwargs):
        self.path = path
        self.realpath = os.path.realpath(path)

        self.mode = mode
        self.uid= uid
        self.gid = gid
        self.checksum = checksum
        self.xattrs = xattrs or dict()

        self.perm_default = "0644"

        self.target = path

        for k, v in kwargs.iteritems():
            self[k] = v

    @classmethod
    def type(cls):
        return cls.filetype

    @classmethod
    def copyable(cls):
        return cls.is_copyable

    @classmethod
    def register(cls, fmaps=FILEINFOS):
        fmaps[cls.type()] = cls

    def __eq__(self, other):
        return self.operations.equals(self, other)

    def equivalent(self, other):
        return self.operations.equivalent(self, other)

    def permission(self):
        return self.operations.permission(self.mode)

    def need_to_chmod(self):
        return self.permission() != self.perm_default

    def need_to_chown(self):
        return self.uid != 0 or self.gid != 0  # 0 == root

    def copy(self, dest, force=False):
        return self.operations.copy(self, dest, force)



class DirInfo(FileInfo):

    operations = DirOperations
    filetype = TYPE_DIR

    def __init__(self, path, mode, uid, gid, checksum, xattrs):
        super(DirInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)
        self.perm_default = "0755"



class SymlinkInfo(FileInfo):

    operations = SymlinkOperations
    filetype = TYPE_SYMLINK

    def __init__(self, path, mode, uid, gid, checksum, xattrs):
        super(SymlinkInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)
        self.linkto = os.path.realpath(path)

    def need_to_chmod(self):
        return False



class OtherInfo(FileInfo):
    """$path may be a socket, FIFO (named pipe), Character Dev or Block Dev, etc.
    """
    filetype = TYPE_OTHER
    is_copyable = False

    def __init__(self, path, mode, uid, gid, checksum, xattrs):
        super(OtherInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)



class UnknownInfo(FileInfo):
    """Special case that lstat() failed and cannot stat $path.
    """
    filetype = TYPE_UNKNOWN
    is_copyable = False

    def __init__(self, path, mode=-1, uid=-1, gid=-1, checksum=checksum(), xattrs={}):
        super(UnknownInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)



FileInfo.register()
DirInfo.register()
SymlinkInfo.register()
OtherInfo.register()
UnknownInfo.register()


# vim: set sw=4 ts=4 expandtab:
