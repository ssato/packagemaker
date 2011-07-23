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
from pmaker.models.DirOperations import *
from pmaker.models.SymlinkOperations import *
from pmaker.models.VirtualFileInfoOperations import *

import logging
import os.path



DICT_0 = dict()
CHECkSUM_0 = checksum()



class FileInfo(object):
    """The class of which objects to hold meta data of regular files, dirs and
    symlinks. This is for regular file and the super class for other types.
    """

    operations = FileOperations
    filetype = TYPE_FILE
    is_copyable = True
    perm_default = "0644"

    def __init__(self, path, mode="0644", uid=0, gid=0, checksum=CHECkSUM_0,
            xattrs=DICT_0, **kwargs):
        """

        @path  str   Target object's path
        @mode  str   File mode e.g. "0644", "1755"
        @uid   int   User ID of the object's owner
        @gid   int   Group ID of the object's owner
        @checksum  str  Checksum of this target object
        @xattr dict  Parameter names and values represent eXtended ATTRibutes
        """
        self.path = path
        self.realpath = os.path.realpath(path)

        self.mode = mode
        self.uid= uid
        self.gid = gid
        self.checksum = checksum
        self.xattrs = xattrs

        self.target = self.dest = path

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @classmethod
    def type(cls):
        return cls.filetype

    @classmethod
    def copyable(cls):
        return cls.is_copyable

    def isfile(self):
        return self.type() == TYPE_FILE

    def __eq__(self, other):
        return self.operations.equals(self, other)

    def permission(self):
        return self.mode

    def need_to_chmod(self):
        return self.permission() != self.perm_default

    def need_to_chown(self):
        return self.uid != 0 or self.gid != 0  # 0 == root

    def copy(self, dest, force=False):
        return self.operations.copy(self, dest, force)



class DirInfo(FileInfo):

    operations = DirOperations
    filetype = TYPE_DIR
    perm_default = "0755"



class SymlinkInfo(FileInfo):

    operations = SymlinkOperations
    filetype = TYPE_SYMLINK

    def __init__(self, path, *args, **kwargs):
        super(SymlinkInfo, self).__init__(path, *args, **kwargs)
        self.linkto = os.path.realpath(path)

    def need_to_chmod(self):
        return False



class OtherInfo(FileInfo):
    """$path may be a socket, FIFO (named pipe), Character Dev or Block Dev, etc.
    """
    filetype = TYPE_OTHER
    is_copyable = False



class UnknownInfo(FileInfo):
    """Special case that lstat() failed and cannot stat $path.
    """
    filetype = TYPE_UNKNOWN
    is_copyable = False

    def __init__(self, path, *args, **kwargs):
        super(UnknownInfo, self).__init__(path, *args, **kwargs)



class VirtualFileInfo(FileInfo):
    """Special type of fileinfo class to accomplish dynamically generated
    files/dirs/symlinks.

    This is for files.
    """
    operations = VirtualFileOperations

    def __init__(self, path, *args, **kwargs):
        super(VirtualFileInfo, self).__init__(path, *args, **kwargs)



class VirtualDirInfo(DirInfo):
    """Likewise but this is for dirs.
    """
    operations = VirtualDirOperations

    def __init__(self, path, *args, **kwargs):
        super(VirtualDirInfo, self).__init__(path, *args, **kwargs)



class VirtualSymlinkInfo(SymlinkInfo):
    """Likewise but this is for symlinks.
    """
    operations = VirtualSymlinkOperations

    def __init__(self, path, *args, **kwargs):
        super(VirtualSymlinkInfo, self).__init__(path, *args, **kwargs)



def init(fileinfo_map=FILEINFOS):
    """FIXME: Ugly
    """
    for cls in (FileInfo, DirInfo, SymlinkInfo, OtherInfo, UnknownInfo):
        fileinfo_map[cls.type()] = cls


# vim: set sw=4 ts=4 expandtab:
