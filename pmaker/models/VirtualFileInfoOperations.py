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
from pmaker.models.DirOperations import DirOperations
from pmaker.models.SymlinkOperations import SymlinkOperations
from pmaker.globals import *

import logging
import os



class VirtualFileOperations(FileOperations):

    @classmethod
    def copy_main(cls, fileinfo, dest, *args, **kwargs):
        """
        Generate target from fileinfo's metadata.
        """
        content = getattr(fileinfo, "content", "")
        open(dest, "wb").write(content)



class VirtualDirOperations(DirOperations):

    @classmethod
    def copy_main(cls, fileinfo, dest, *args, **kwargs):
        try:
            mode = int(fileinfo.permission(), 8)
            os.makedirs(dest, mode)

        # Maybe OK: target dir should be created but failed to set stats.
        except OSError, e:
            pass



class VirtualSymlinkOperations(SymlinkOperations):

    @classmethod
    def copy_main(cls, fileinfo, dest, *args, **kwargs):
        os.symlink(fileinfo.linkto, dest)


# vim: set sw=4 ts=4 expandtab:
