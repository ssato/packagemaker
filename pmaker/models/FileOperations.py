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
from pmaker.utils import *  # dicts_comp
from pmaker.shell import shell

import logging
import os
import os.path
import shutil
import stat


if PYXATTR_ENABLED:
    import xattr  # pyxattr
else:
    # Make up a "Null-Object" like class mimics xattr module.
    class xattr(object):
        def set(self, *args, **kwargs):
            pass



class FileOperations(object):
    """Class to implement operations for FileInfo classes.

    This class will not be instatiated and mixed into FileInfo classes.
    """

    @classmethod
    def equals(cls, lhs, rhs):
        """lhs and rhs are identical, that is, these contents and metadata
        (except for path) are exactly same.

        TODO: Compare the part of the path?
          ex. lhs.path: "/path/to/xyz", rhs.path: "/var/lib/sp2/updates/path/to/xyz"

        >>> lhs = FileInfoFactory().create("/etc/resolv.conf")
        >>> rhs = copy.copy(lhs)
        >>> setattr(rhs, "other_attr", "xyz")
        >>> 
        >>> FileOperations.equals(lhs, rhs)
        True
        >>> rhs.mode = "755"
        >>> FileOperations.equals(lhs, rhs)
        False
        """
        keys = ("mode", "uid", "gid", "checksum", "filetype")
        res = all(getattr(lhs, k) == getattr(rhs, k) for k in keys)

        return res and dicts_comp(lhs.xattrs, rhs.xattrs) or False

    @classmethod
    def equivalent(cls, lhs, rhs):
        """These metadata (path, uid, gid, etc.) do not match but the checksums
        are same, that is, that contents are exactly same.

        @lhs  FileInfo object
        @rhs  Likewise

        >>> class FakeFileInfo(object):
        ...     checksum = checksum()
        >>> 
        >>> lhs = FakeFileInfo(); rhs = FakeFileInfo()
        >>> FileOperations.equivalent(lhs, rhs)
        True
        >>> rhs.checksum = checksum("/etc/resolv.conf")
        >>> FileOperations.equivalent(lhs, rhs)
        False
        """
        return lhs.checksum == rhs.checksum

    @classmethod
    def permission(cls, mode):
        """permission (mode) can be passed to "chmod".

        NOTE: There are some special cases, e.g. /etc/gshadow- and
        /etc/shadow-, such that mode == 0.

        @mode  stat.mode

        >>> file0 = "/etc/resolv.conf"
        >>> if os.path.exists(file0):
        ...     mode = os.lstat(file0).st_mode
        ...     expected = oct(stat.S_IMODE(mode & 0777))
        ...     assert expected == FileOperations.permission(mode)
        >>> 
        >>> gshadow = "/etc/gshadow-"
        >>> if os.path.exists(gshadow):
        ...     mode = os.lstat(gshadow).st_mode
        ...     assert "0000" == FileOperations.permission(mode)
        """
        m = stat.S_IMODE(mode & 0777)
        return m == 0 and "0000" or oct(m)

    @classmethod
    def copy_main(cls, fileinfo, dest, use_pyxattr=PYXATTR_ENABLED):
        """Two steps needed to keep the content and metadata of the original file:

        1. Copy itself and its some metadata (owner, mode, etc.)
        2. Copy extra metadata not copyable with the above.

        "cp -a" (cp in GNU coreutils) does the above operations at once and
        might be suited for most cases, I think.

        @fileinfo   FileInfo object
        @dest  str  Destination path to copy to
        @use_pyxattr bool  Whether to use pyxattr module
        """
        if use_pyxattr:
            shutil.copy2(fileinfo.path, dest)  # correponding to "cp -p ..."
            cls.copy_xattrs(fileinfo.xattrs, dest)
        else:
            shell("cp -a %s %s" % (fileinfo.path, dest))

    @classmethod
    def copy_xattrs(cls, src_xattrs, dest):
        """
        @src_xattrs  dict  Xattributes of source FileInfo object to copy
        @dest        str   Destination path
        """
        for k, v in src_xattrs.iteritems():
            xattr.set(dest, k, v)

    @classmethod
    def remove(cls, path):
        os.remove(path)

    @classmethod
    def copy(cls, fileinfo, dest, force=False):
        """Copy to $dest.  "Copy" action varys depends on actual filetype so
        that inherited class must overrride this and related methods (_remove
        and _copy).

        @fileinfo  FileInfo  FileInfo object
        @dest      string    The destination path to copy to
        @force     bool      When True, force overwrite $dest even if it exists
        """
        assert fileinfo.path != dest, "Copying src and dst are same!"

        if not fileinfo.copyable():
            logging.warn(" Not copyable: %s" % str(fileinfo))
            return False

        if os.path.exists(dest):
            logging.warn(" Copying destination already exists: '%s'" % dest)

            # TODO: It has negative impact for symlinks.
            #
            #if os.path.realpath(self.path) == os.path.realpath(dest):
            #    logging.warn("Copying src and dest are same actually.")
            #    return False

            if force:
                logging.info(" Removing old one before copying: " + dest)
                fileinfo.operations.remove(dest)
            else:
                logging.warn(" Do not overwrite it")
                return False
        else:
            destdir = os.path.dirname(dest)

            # TODO: which is better?
            #os.makedirs(os.path.dirname(dest)) or ...
            #shutil.copytree(os.path.dirname(self.path), os.path.dirname(dest))

            if not os.path.exists(destdir):
                os.makedirs(destdir)
            shutil.copystat(os.path.dirname(fileinfo.path), destdir)

        logging.debug(" Copying from '%s' to '%s'" % (fileinfo.path, dest))
        cls.copy_main(fileinfo, dest)

        return True


# vim: set sw=4 ts=4 expandtab:
