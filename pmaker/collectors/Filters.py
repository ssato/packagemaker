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
from pmaker.globals import TYPES_SUPPORTED
from pmaker.models.FileInfo import FileInfo

import logging
import os


class BaseFilter(object):
    """Base class to filter out specific FileInfo objects and make them not
    collected when Collector.collect() runs.
    """
    _reason = ""

    def __init__(self, *args, **kwargs):
        pass

    def pre(self, fileinfo):
        assert isinstance(fileinfo, FileInfo)

    def post(self, fileinfo):
        msg = "Filtered out as %s: path=%s, type=%s" % \
            (self._reason, fileinfo.path, fileinfo.type())

        logging.warn(msg)

    def _pred(self, fileinfo):
        #return False  # NOTE: It will not be filtered out if False.
        raise NotImplementedError("Child classes must override this method!")

    def pred(self, fileinfo, *args, **kwargs):
        """
        @fileinfo  FileInfo object
        """
        self.pre(fileinfo)
        ret = self._pred(fileinfo)

        if ret:
            self.post(fileinfo)

        return ret

    def __call__(self, fileinfo, *args, **kwargs):
        return self.pred(fileinfo, *args, **kwargs)


class UnsupportedTypesFilter(BaseFilter):
    """A filter class to filter out fileinfo objects of which type is not
    supported.
    """

    _reason = "not supported type"

    def _pred(self, fileinfo):
        """Rule to filter out fileinfo objects if its type is not supported.
        """
        return fileinfo.type() not in TYPES_SUPPORTED


class ReadAccessFilter(BaseFilter):
    """A filter class to filter out fileinfo objects of which type is not
    supported.
    """

    _reason = "You don't have read access"

    def _pred(self, fileinfo):
        return not fileinfo.create and not os.access(fileinfo.path, os.R_OK)


# vim:sw=4 ts=4 et:
