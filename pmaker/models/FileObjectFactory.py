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
from pmaker.models.Bunch import Bunch

import pmaker.utils as U
import pmaker.models.FileObjects as FO

import logging
import os
import os.path
import stat


def lstat(path):
    """
    stat the path to get file metadata.

    :param path:  Object's path (relative or absolute) :: str
    :return:  A tuple of (mode, uid, gid) or (None, None, None)
              if OSError was raised.
    """
    try:
        st = os.lstat(path)
    except OSError, e:
        logging.warn(e)
        return None

    return (st.st_mode, st.st_uid, st.st_gid)


def guess_filetype(st_mode):
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


def create_from_real_object(fo):
    """
    Creates and returns an appropriate type of FileObjects' instance from a
    FileObject's instance. The entity of FileObject's instance must exists.

    :param fo:  A FileObjects.XObject's instance
    """
    assert os.path.exists(fo.path)

    basic_attr_names = ("mode", "uid", "gid")
    st = lstat(fo.path)

    if st is None:
        return FO.UnknownObject(**fo)

    attrs = dict(zip(basic_attr_names, st))
    attrs["mode"] = U.st_mode_to_mode(attrs["mode"])

    filetype = guess_filetype(st[0])

    if filetype == TYPE_FILE:
        fo.checksum = U.checksum(fo.path)
    else:
        fo.checksum = U.checksum()

        if filetype == TYPE_UNKNOWN:
            logging.warn(" Failed to detect filetype: " + fo.path)

        elif filetype == TYPE_SYMLINK:
            if not fo.get("linkto", False):
                fo.linkto = os.path.realpath(fo.path)

    # override with real (stat-ed) values if not specified.
    for n in basic_attr_names:
        if not fo.get(n, False):
            fo[n] = attrs[n]

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
        if os.path.exists(fo.path):
            return create_from_real_object(fo)
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

    # set default values to necessary parameters if not set:
    for attr in ("mode", "uid", "gid", "checksum"):
        if not fo.get(attr, False):
            fo[attr] = fo.defaults[attr]

    cls = FO.FILEOBJECTS.get(filetype, None)
    assert cls is not None

    return cls(**fo)


# vim:sw=4 ts=4 et:
