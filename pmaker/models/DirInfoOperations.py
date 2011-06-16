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
from pmaker.models.FileInfoOperations import FileOperations

import logging
import os
import os.path
import shutil



class DirOperations(FileOperations):

    @classmethod
    def remove(cls, path):
        if not os.path.isdir(path):
            raise RuntimeError(" '%s' is not a directory! Aborting..." % path)

        os.removedirs(path)

    @classmethod
    def copy_main(cls, fileinfo, dest, use_pyxattr=False):
        try:
            mode = int(fileinfo.permission(), 8)  # in octal, e.g. 0755
            os.makedirs(dest, mode)

        except OSError, e:   # It may be OK, ex. non-root user cannot set perms.
            logging.debug("Failed: os.makedirs, dest=%s, mode=%o" % (dest, mode))
            logging.warn(e)

            logging.info("skip to copy " + dest)

            # FIXME: What can be done with it?
            #
            #if not os.path.exists(dest):
            #    os.chmod(dest, os.lstat(dest).st_mode | os.W_OK | os.X_OK)
            #    os.makedirs(dest, mode)

        uid = os.getuid()
        gid = os.getgid()

        if uid == 0 or (uid == fileinfo.uid and gid == fileinfo.gid):
            os.chown(dest, fileinfo.uid, fileinfo.gid)
        else:
            logging.debug("Chown is not permitted so do not")

        shutil.copystat(fileinfo.path, dest)
        cls.copy_xattrs(fileinfo.xattrs, dest)


# vim: set sw=4 ts=4 expandtab:
