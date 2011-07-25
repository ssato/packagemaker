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
from pmaker.utils import *  # import 'all' if not pre-defined.
from pmaker.shell import shell

import logging
import os
import os.path
import shutil



class FileOperations(object):
    """Class to implement operations for FileInfo classes.

    This class will not be instatiated and mixed into FileInfo classes.
    """

    @classmethod
    def equals(cls, lhs, rhs):
        """lhs and rhs are identical, that is, these contents and metadata
        (except for path) are exactly same.

        TODO: Compare the part of the path?
          ex. lhs.path: "/path/to/xyz", rhs.path: "/var/lib/save.d/path/to/xyz"
        """
        keys = ("mode", "uid", "gid", "checksum", "filetype")
        res = all(getattr(lhs, k) == getattr(rhs, k) for k in keys)

        return res or False

    @classmethod
    def copy_main(cls, fileinfo, dest):
        """Two steps needed to keep the content and metadata of the original file:

        1. Copy itself and its some metadata (owner, mode, etc.)
        2. Copy extra metadata not copyable with the above.

        "cp -a" (cp in GNU coreutils) does the above operations at once and
        might be suited for most cases, I think.

        @fileinfo   FileInfo object
        @dest  str  Destination path to copy to
        """
        shell("cp -a %s %s" % (fileinfo.path, dest))

    @classmethod
    def create(cls, fileinfo, dest):
        open(dest, "w").write(fileinfo.content)

    @classmethod
    def remove(cls, path):
        os.remove(path)

    @classmethod
    def copy(cls, fileinfo, dest, force=False):
        """Copy to $dest.  "Copy" action varys depends on actual filetype so
        that inherited class must overrride this and related methods.

        @fileinfo  FileInfo  FileInfo object
        @dest      string    The destination path to copy to
        @force     bool      When True, force overwrite $dest even if it exists
        """
        create_instead_of_copy = fileinfo.create

        if not create_instead_of_copy:
            assert fileinfo.path != dest, "Copying src and dst are same!"

            if not fileinfo.copyable():
                logging.warn(" Not copyable: %s" % str(fileinfo))
                return False

        if os.path.exists(dest):
            logging.warn(" Destination already exists: " + dest)

            if force:
                logging.info(" Removing old one in advance: " + dest)
                cls.remove(dest)
            else:
                logging.warn(" Do not overwrite it")
                return False
        else:
            destdir = os.path.dirname(dest)

            if not os.path.exists(destdir):
                os.makedirs(destdir)

            if not create_instead_of_copy:
                try:
                    shutil.copystat(os.path.dirname(fileinfo.path), destdir)
                except OSError:
                    logging.warn("Could not copy stat of " + os.path.dirname(fileinfo.path))

        if create_instead_of_copy:
            logging.debug(" Creating " + dest)
            cls.create(fileinfo, dest)
        else:
            logging.debug(" Copying from %s to %s" % (fileinfo.path, dest))
            cls.copy_main(fileinfo, dest)

        return True

# vim: set sw=4 ts=4 expandtab:
