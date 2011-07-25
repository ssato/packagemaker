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
from pmaker.globals import *  # CONFLICTS_SAVEDIR, CONFLICTS_NEWDIR
from pmaker.collectors.Modifiers import FileInfoModifier
from pmaker.rpmutils import rpm_search_provides_by_path, rpm_attr

import logging
import os.path



class RpmAttributeModifier(FileInfoModifier):
    _priority = 9

    def update(self, fileinfo, *args, **kwargs):
        fileinfo.rpm_attr = rpm_attr(fileinfo)

        return fileinfo



class RpmConflictsModifier(FileInfoModifier):

    _priority = 6

    def __init__(self, package, rpmdb_path=None):
        """
        @package  str  Name of the package to be built
        """
        self.package = package

        self.savedir = CONFLICTS_SAVEDIR % {"name": package}
        self.newdir = CONFLICTS_NEWDIR % {"name": package}

    def find_owner(self, path):
        """Find the package owns given path.

        @path  str  File/dir/symlink path
        """
        owner_nvrae = rpm_search_provides_by_path(path)

        if owner_nvrae and owner_nvrae["name"] != self.package:
            logging.warn("%s is owned by %s" % (path, owner_nvrae["name"]))
            return owner_nvrae
        else:
            return dict()

    def update(self, fileinfo, *args, **kwargs):
        fileinfo.conflicts = self.find_owner(fileinfo.target)

        if fileinfo.conflicts:
            fileinfo.original_path = fileinfo.install_path

            path = fileinfo.install_path[1:]  # strip "/" at the head.
            fileinfo.target = fileinfo.install_path = os.path.join(self.newdir, path)
            fileinfo.save_path = os.path.join(self.savedir, path)

        return fileinfo


# vim: set sw=4 ts=4 expandtab:
