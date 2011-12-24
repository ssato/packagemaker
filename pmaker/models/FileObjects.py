#
# Copyright (C) 2011 Satoru SATOH <satoru.satoh @ gmail.com>
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
#
from pmaker.globals import TYPE_FILE, TYPE_DIR, TYPE_SYMLINK, \
    TYPE_OTHER, TYPE_UNKNOWN

from pmaker.utils import checksum
from pmaker.models.Bunch import Bunch
from pmaker.models.FileObjectOperations import FileOps, DirOps, SymlinkOps

import copy
import os.path


class InvalidFileTypeError(RuntimeError):
    pass


def typestr_to_type(s):
    """
    Convert string representation of type to TYPE_*.
    """
    typemap = dict(
        f=TYPE_FILE, d=TYPE_DIR, s=TYPE_SYMLINK,
        o=TYPE_OTHER, u=TYPE_UNKNOWN
    )

    filetype = typemap.get(s[0], None)

    if filetype is None:
        raise InvalidFileTypeError("filetype=" + s)

    return filetype


class XObject(Bunch):
    """
    This class represents regular files, dirs, symlinks and other objects on
    filesystem.

    This class is for regular file and the super class for other types at the
    same time.
    """

    defaults = Bunch(mode="0644", uid=0, gid=0, checksum=checksum())

    def __init__(self, path=None, mode=None, uid=None, gid=None,
            checksum=None, create=False, content="", src=None,
            **kwargs):
        """
        :param path: Target object's path :: str
        :param mode: File mode, e.g. "0644", "1755" :: str
        :param uid:  User ID of the object's owner :: int
        :param gid:  Group ID of the object's owner :: int
        :param checksum:  Checksum of this file object
        :param create:    If true, the file object will be substantialized on
                          dest dynamically.
        :param content:   The string represents the content of path to create.
        :param src:  Path or URL to the actual location of the file object.
        """
        assert path is not None, "Path must not be None!"  # MUST

        self.path = path
        self.mode = self.defaults.mode if mode is None else mode
        self.uid = self.defaults.uid if uid is None else uid
        self.gid = self.defaults.gid if gid is None else gid
        self.checksum = self.defaults.checksum if checksum is None else checksum
        self.create = bool(create)
        self.content = content
        self.src = path if src is None else src

        self.target = self.install_path = path

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def equals(self, other):
        ckeys = ("path",
                 "mode",
                 "uid",
                 "gid",
                 "checksum",
                 "content",
                 "src",
                 "install_path"
        )
        return all(
            getattr(self, k, None) == getattr(other, k, None) for k in ckeys
        )


class FileObject(XObject):
    """File object
    """

    ops = FileOps
    filetype = TYPE_FILE
    is_copyable = True

    @classmethod
    def type(cls):
        return cls.filetype

    @classmethod
    def copyable(cls):
        return cls.is_copyable

    @classmethod
    def isfile(cls):
        return cls.type() == TYPE_FILE

    def __cmp__(self, other):
        return cmp(self.path, other.path)

    def __eq__(self, other):
        return self.equals(other)

    def permission(self):
        return self.mode

    def need_to_chmod(self):
        return self.mode != self.defaults.mode

    def need_to_chown(self):
        return self.uid != 0 or self.gid != 0  # 0 == root

    def copy(self, dest, force=False):
        return self.ops.copy(self, dest, force)


class DirObject(FileObject):

    ops = DirOps
    filetype = TYPE_DIR

    defaults = copy.copy(XObject.defaults)
    defaults.mode = "0755"


class SymlinkObject(FileObject):

    ops = SymlinkOps
    filetype = TYPE_SYMLINK

    def __init__(self, path, linkto=None, **kwargs):
        """
        :param linkto: The path to link to :: str
        """
        super(SymlinkObject, self).__init__(path, **kwargs)
        self.linkto = linkto

    def need_to_chmod(self):
        return False


class OtherObject(FileObject):
    """
    May be a socket, FIFO (named pipe), Character Dev or Block Dev, etc.
    """

    filetype = TYPE_OTHER
    is_copyable = False


class UnknownObject(FileObject):
    """
    Special case that lstat() failed and cannot stat $path.
    """

    filetype = TYPE_UNKNOWN
    is_copyable = False


FILEOBJECTS = dict(
    (cls.type(), cls) for cls in \
        (FileObject, DirObject, SymlinkObject, OtherObject, UnknownObject)
)


# vim:sw=4 ts=4 et:
