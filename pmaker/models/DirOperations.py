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
from pmaker.models.FileOperations import FileOperations

import logging
import os
import os.path
import shutil


class DirOperations(FileOperations):

    @classmethod
    def remove(cls, path):
        assert os.path.isdir(path), "Not a directory! path=" + path
        os.removedirs(path)

    @classmethod
    def create(cls, fileinfo, dest):
        try:
            mode = int(fileinfo.permission(), 8)  # in octal, e.g. 0755
            os.makedirs(dest, mode)

        except OSError, e:   # It may be OK, ex. !root user cannot set perms.
            logging.debug(
                " Failed: os.makedirs, dest=%s, mode=%o" % (dest, mode)
            )
            logging.warn(e)
            logging.info(" Skipped: " + dest)

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
            logging.debug("Chown is not permitted so do nothing")

    @classmethod
    def copy_main(cls, fileinfo, dest):
        cls.create(fileinfo, dest)

        try:
            shutil.copystat(fileinfo.path, dest)
        except OSError, e:
            logging.warn(str(e))


# vim:sw=4 ts=4 et:
