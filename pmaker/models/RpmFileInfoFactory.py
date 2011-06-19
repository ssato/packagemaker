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
from pmaker.models.FileInfoFactory import FileInfoFactory
from pmaker.rpmutils import info_by_path

import grp
import pwd



class RpmFileInfoFactory(FileInfoFactory):

    def _stat(self, path):
        """Stat with using RPM database instead of lstat().

        There are cases to get no results if the target objects not owned by
        any packages.
        """
        try:
            fi = info_by_path(path)
            if fi:
                uid = pwd.getpwnam(fi["uid"]).pw_uid   # uid: name -> id
                gid = grp.getgrnam(fi["gid"]).gr_gid   # gid: name -> id

                return (fi["mode"], uid, gid)
        except:
            pass

        return super(RpmFileInfoFactory, self)._stat(path)


# vim: set sw=4 ts=4 expandtab:
