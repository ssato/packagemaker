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
import pmaker.globals as G
import pmaker.models.Bunch as B
import pmaker.models.FileObjects as FO
import pmaker.rpmutils as R
import pmaker.utils as U

import grp
import logging
import os
import os.path
import pwd
import stat


def rpm_lstat(path):
    """Stat with using RPM database instead of lstat().

    There are cases to get no results if the target objects not owned by
    any packages.
    """
    try:
        fi = R.info_by_path(path)
        if fi:
            uid = pwd.getpwnam(fi["uid"]).pw_uid   # uid: name -> id
            gid = grp.getgrnam(fi["gid"]).gr_gid   # gid: name -> id

            return (fi["mode"], uid, gid)
    except:
        return None


def lstat(path, use_rpmdb=False):
    """
    stat the path to get file metadata.

    :param path:  Object's path (relative or absolute) :: str
    :param use_rpmdb:  Whether to use rpm database or not :: bool
    :return:  A tuple of (mode, uid, gid) or (None, None, None)
              if OSError was raised.
    """
    if use_rpmdb:
        if R.is_rpmdb_available():
            st = rpm_lstat(path)
            if st is None:
                logging.info("Not in rpm db. Looks no rpms own " + path)
            else:
                return st
        else:
            logging.warn(
                "use_rpmdb is set but rpm database looks not available."
            )
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
        ft = G.TYPE_SYMLINK

    elif stat.S_ISREG(st_mode):
        ft = G.TYPE_FILE

    elif stat.S_ISDIR(st_mode):
        ft = G.TYPE_DIR

    elif stat.S_ISCHR(st_mode) or stat.S_ISBLK(st_mode) \
        or stat.S_ISFIFO(st_mode) or stat.S_ISSOCK(st_mode):
        ft = G.TYPE_OTHER
    else:
        ft = G.TYPE_UNKNOWN  # Should not be reached here.

    return ft


def create_from_real_object(fo, use_rpmdb=False):
    """
    Creates and returns an appropriate type of FileObjects' instance from a
    Bunch object of which path exists actually.

    :param fo:  A Bunch object
    """
    if not os.path.islink(fo.path):
        assert os.path.exists(fo.path)

    basic_attr_names = ("mode", "uid", "gid")
    st = lstat(fo.path, use_rpmdb)

    if st is None:
        return FO.UnknownObject(**fo)

    attrs = dict(zip(basic_attr_names, st))
    attrs["mode"] = U.st_mode_to_mode(attrs["mode"])

    filetype = guess_filetype(st[0])

    if filetype == G.TYPE_FILE:
        fo.checksum = U.checksum(fo.path)
    else:
        fo.checksum = U.checksum()

        if filetype == G.TYPE_UNKNOWN:
            logging.warn("Failed to detect filetype: " + fo.path)

        elif filetype == G.TYPE_SYMLINK:
            if "linkto" not in fo:
                fo.linkto = os.path.realpath(fo.path)

    # override with real (stat-ed) values if not specified.
    for n in basic_attr_names:
        if n not in fo:
            fo[n] = attrs[n]

    cls = FO.FILEOBJECTS.get(filetype, None)
    assert cls is not None

    return cls(**fo)


def to_be_created(fo):
    return ("content" in fo and fo.content) or "linkto" in fo or \
        ("src" in fo and fo.src != fo.path)


def create(path, use_rpmdb=False, **attrs):
    """
    A kind of factory method to create an appropriate type of FileObjects'
    instance from path.

    :param path:  Path of target object.
    :param attrs: A dict holding metadata other than path such as mode, gid,
                  uid, checksum, create, filetype, src, linkto, etc.
    """
    fo = B.Bunch(path=path, **attrs)

    if "create" in fo and fo.create:
        assert to_be_created(fo), \
            "Missing info to create: path=%s, attrs=%s" % (path, str(attrs))
    else:
        # $path exists or not exist but it's a symlink, link to
        # non-existent-obj to be linked.
        if os.path.exists(path) or os.path.islink(path):
            return create_from_real_object(fo, use_rpmdb)
        else:
            fo.create = True if to_be_created(fo) else False

    if "filetype" in fo:
        filetype = FO.typestr_to_type(fo.filetype)
    else:
        filetype = G.TYPE_UNKNOWN

        if ("content" in fo and fo.content) or \
                ("src" in fo and fo.src != fo.path):
            filetype = G.TYPE_FILE

        elif "linkto" in fo:
            filetype = G.TYPE_SYMLINK

        else:  # TODO: Is there any specific features in dirs?
            filetype = G.TYPE_DIR

    #logging.debug("xo=" + str(fo))

    cls = FO.FILEOBJECTS.get(filetype, None)
    assert cls is not None

    return cls(**fo)


# vim:sw=4 ts=4 et:
