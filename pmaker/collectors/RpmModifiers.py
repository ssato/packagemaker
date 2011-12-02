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
import pmaker.collectors.Modifiers as M
import pmaker.rpmutils as R
import pmaker.utils as U

import logging
import os.path


class RpmAttributeModifier(M.FileInfoModifier):
    _priority = 9

    def update(self, fo, *args, **kwargs):
        """
        :param fo: FileObject or FileInfo instance represents files.
        """
        fo.rpm_attr = R.rpm_attr(fo)

        return fo


class RpmConflictsModifier(M.FileInfoModifier):

    _priority = 6

    def __init__(self, name, rpmdb_path=None):
        """
        :param name: The name of this package to be built.
        """
        self.name = name
        (self.savedir, self.newdir) = U.conflicts_dirs(name)

    def find_owner(self, path):
        """Find packages own given path, i.e. will conflict with.

        :param path: Path of target file/dir/symlink.
        """
        owner_nvrae = R.rpm_search_provides_by_path(path)

        if owner_nvrae and owner_nvrae["name"] != self.name:
            logging.warn("%s is owned by %s" % (path, owner_nvrae["name"]))
            return owner_nvrae
        else:
            return dict()

    def update(self, fo, *args, **kwargs):
        fo.conflicts = self.find_owner(fo.install_path)

        if fo.conflicts:
            fo.original_path = fo.install_path

            path = fo.install_path[1:]  # strip "/" at the head.

            fo.install_path = os.path.join(self.newdir, path)
            fo.save_path = os.path.join(self.savedir, path)

        return fo


# vim:sw=4 ts=4 et:
