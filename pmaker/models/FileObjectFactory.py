#
# Copyright (C) 2011 Satoru SATOH <ssato @ redhat.com>
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
from pmaker.globals import TYPE_FILE, TYPE_DIR, TYPE_SYMLINK, \
    TYPE_OTHER, TYPE_UNKNOWN

import pmaker.utils as U
import pmaker.models.FileObjects as FO

import logging
import os
import os.path
import stat


def __stat(path):
    """
    stat the path to get file metadata.

    :param path:  Object's path (relative or absolute) :: str
    :return:  A tuple of (mode, uid, gid) or (None, None, None)
              if OSError was raised.
    """
    try:
        _stat = os.lstat(path)
    except OSError, e:
        logging.warn(e)
        return None

    return (_stat.st_mode, _stat.st_uid, _stat.st_gid)


def __guess_filetype(st_mode):
    """
    Guess file type by st_mode.

    :param st_mode:  stat.st_mode
    """
    if stat.S_ISLNK(st_mode):
        ft = TYPE_SYMLINK

    elif stat.S_ISREG(st_mode):
        ft = TYPE_FILE

    elif stat.S_ISDIR(st_mode):
        ft = TYPE_DIR

    elif stat.S_ISCHR(st_mode) or stat.S_ISBLK(st_mode) \
        or stat.S_ISFIFO(st_mode) or stat.S_ISSOCK(st_mode):
        ft = TYPE_OTHER
    else:
        ft = TYPE_UNKNOWN  # Should not be reached here.

    return ft


def __create_from_path(fo):
    """
    Creates and returns an appropriate type of FileObjects' instance from a
    FileObject's instance. The entity of FileObject's instance must exists.

    :param fo:  A FileObjects.XObject's instance
    """
    assert os.path.exists(fo.path)

    st = __stat(fo.path)

    if st is None:
        return FO.UnknownObject(**fo)

    basic_attr_names = ("mode", "uid", "gid")

    attrs = dict(zip(basic_attr_names, st))
    attrs["mode"] = U.st_mode_to_mode(real_attrs["mode"])

    filetype = __guess_filetype(real_st_mode)

    if filetype == TYPE_FILE:
        fo.checksum = U.checksum(fo.path)
    else:
        if filetype == TYPE_UNKNOWN:
            logging.warn(" Failed to resolve filetype: " + fo.path)

        elif filetype == TYPE_SYMLINK:
            if not fo.get("linkto", False):
                fo.linkto = os.path.realpath(fo.path)

    # override with real (stat-ed) values if not specified.
    for n in basic_attr_names:
        fo[n] = fo.get(n, attrs[n])

    cls = FO.FILEOBJECTS.get(filetype, None)
    assert cls is not None

    return cls(**fo)


def create(path, **attrs):
    """
    A kind of factory method to create an appropriate type of FileObjects'
    instance from path.

    :param path:  Path of target object.
    :param attrs: A dict holding metadata other than path such as mode, gid,
                  uid, checksum, create, filetype, src, linkto, etc.
    """
    fo = FO.XObject(path, **attrs)

    if not fo.create:
        if os.path.exists(path):
            return __create_from_path(fo)
        else:
            fo.create = True

    if "filetype" in fo:
        filetype = FO.typestr_to_type(fo.filetype)
    else:
        if fo.content or fo.src != fo.path:
            filetype = TYPE_FILE

        elif "linkto" in fo:
            filetype = TYPE_SYMLINK

        else:  # TODO: Is there any specific features in dirs?
            filetype = TYPE_DIR

    cls = FO.FILEOBJECTS.get(filetype, None)
    assert cls is not None

    return cls(**fo)


# vim:sw=4 ts=4 et:
