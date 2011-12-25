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
from pmaker.models.FileObjects import FileObject

import logging
import os


class BaseFilter(object):
    """
    Base class to filter out specific FileObjects' objects and make them not
    collected when Collector.collect() runs.
    """
    _reason = ""

    def __init__(self, *args, **kwargs):
        pass

    def pre(self, f):
        assert isinstance(f, FileObject)

    def post(self, f):
        msg = "Filtered out as %s: path=%s, type=%s" % \
            (self._reason, f.path, f.type())

        logging.warn(msg)

    def _pred(self, fileinfo):
        #return False  # NOTE: It will not be filtered out if False.
        raise NotImplementedError("Child classes must override this method!")

    def pred(self, f, *args, **kwargs):
        """
        :param f: FileObject instance
        """
        self.pre(f)
        ret = self._pred(f)

        if ret:
            self.post(f)

        return ret

    def __call__(self, f, *args, **kwargs):
        return self.pred(f, *args, **kwargs)


class UnsupportedTypesFilter(BaseFilter):
    """
    A filter class to filter out files of which type is not supported.
    """

    _reason = "not supported type"

    def _pred(self, f):
        """Rule to filter out files if its type is not supported.
        """
        return f.type() not in TYPES_SUPPORTED


class NotExistFilter(BaseFilter):
    """
    A filter to filter out files not exist and not created later.
    """

    _reason = "not exist"

    def _pred(self, f):
        return not f.create and not os.path.exists(f.path)


class ReadAccessFilter(BaseFilter):
    """
    A filter class to filter out files of which type is not supported.
    """

    _reason = "not permitted to read"

    def _pred(self, f):
        return not f.create and not os.access(f.path, os.R_OK)


# vim:sw=4 ts=4 et:
