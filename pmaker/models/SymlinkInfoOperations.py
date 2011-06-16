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
from pmaker.models.FileInfoOperations import FileOperations
from pmaker.shell import shell

import os



class SymlinkOperations(FileOperations):

    link_instead_of_copy = False

    @classmethod
    def copy_main(cls, fileinfo, dest, use_pyxattr=False):
        if cls.link_instead_of_copy:
            os.symlink(fileinfo.linkto, dest)
        else:
            shell("cp -a %s %s" % (fileinfo.path, dest))


# vim: set sw=4 ts=4 expandtab:
