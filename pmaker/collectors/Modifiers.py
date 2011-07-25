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
import logging
import os.path



class FileInfoModifier(object):
    """
    Base class to transform some specific attributes of FileInfo objects during
    Collector.collect().
    """

    _priority = 0

    def __init__(self, *args, **kwargs):
        pass

    def __cmp__(self, other):
        return cmp(self._priority, other._priority)

    def update(self, fileinfo, *args, **kwargs):
        """This method is just a template and returns given fileinfo w/ no
        modification.

        @fileinfo FileInfo object
        @target   Target objecr
        """
        return fileinfo



class DestdirModifier(FileInfoModifier):

    _priority = 1

    def __init__(self, destdir):
        self.destdir = destdir

    def rewrite_with_destdir(self, path):
        """
        Rewrite target, destination path to install, by assuming path is
        consist of DESTDIR and actual installation path, that is, DESTDIR will
        be stripped.

        >>> dm = DestdirModifier
        >>> assert dm("/a/b").rewrite_with_destdir("/a/b/c") == "/c"
        >>> assert dm("/a/b/").rewrite_with_destdir("/a/b/c") == "/c"
        >>> try:
        ...     dm("/x/y").rewrite_with_destdir("/a/b/c")
        ... except RuntimeError, e:
        ...     pass
        """
        if path.startswith(self.destdir):
            new_path = path.split(self.destdir)[1]

            if not new_path.startswith(os.path.sep):
                new_path = os.path.sep + new_path

            logging.debug("Rewrote installation path from %s to %s" % (path, new_path))
            return new_path
        else:
            logging.error(" The path '%s' does not start with '%s'" % (path, self.destdir))
            raise RuntimeError("Destdir and the actual file path are inconsistent.")

    def update(self, fileinfo, *args, **kwargs):
        fileinfo.target = fileinfo.install_path = self.rewrite_with_destdir(fileinfo.path)
        return fileinfo



class OwnerModifier(FileInfoModifier):

    _priority = 5

    def __init__(self, owner_uid=0, owner_gid=0):
        self.uid = owner_uid
        self.gid = owner_gid

    def update(self, fileinfo, *args, **kwargs):
        fileinfo.uid = self.uid
        fileinfo.gid = self.gid

        return fileinfo



class AttributeModifier(FileInfoModifier):

    _priority = 9

    def update(self, fileinfo, attrs=dict(), *args, **kwargs):
        """
        @fileinfo  FileInfo object
        @attrs     FileInfo attributes to overwrite
        """
        for attr, val in attrs.iteritems():
            if attr == "path":  # fileinfo.path must not be overridden.
                logging.warn("You cannot overwrite path: path=" + fileinfo.path)
                continue

            logging.info("Override %s=%s: path=%s" % (attr, val, fileinfo.path))
            setattr(fileinfo, attr, val)

        return fileinfo


# vim: set sw=4 ts=4 expandtab:
