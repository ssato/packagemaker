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
from pmaker.shell import run

import logging
import os
import os.path
import re
import shutil
import urllib2

try:
    all
except NameError:
    from pmaker.utils import all


def same(lhs, rhs):
    """
    lhs and rhs are identical, that is, these contents and metadata (except
    for path) are exactly same.
    """
    return all(
        getattr(lhs, k) == getattr(rhs, k) for k in \
            ("mode", "uid", "gid", "checksum", "filetype")
    )


def equals(lhs, rhs):
    """
    Along with the above, paths of them are same.
    """
    return lhs.path == rhs.path and same(lhs, rhs)


def __id(x):
    return x


URL_PATTERN = re.compile(r"(http|https|ftp)://\S+")


def is_url(s):
    """

    >>> is_url("ftp://ftp.example.com")
    True
    >>> is_url("http://www.example.com")
    True
    >>> is_url("https://www.example.com")
    True
    >>> is_url("http://www.example.com/a/b/c/d?x=1&y=2&z=3")
    True
    >>> is_url("/a/b/c")
    False
    """
    return URL_PATTERN.match(s) is not None


def fetch(src):
    """
    Fetch the content of $src. $src may be a URL or file path.

    FIXME: This method may block main thread for a while.

    @throw urllib2.URLError, IOError, etc.
    """
    if is_url(src):
        response = urllib2.urlopen(src)
        return response.read()
    else:
        return open(src).read()


class FileOps(object):
    """This class implements file operations.

    This class should not be instantiated and be mixed into classes in
    FileObjects module.
    """
    @classmethod
    def remove(cls, path):
        os.remove(path)

    @classmethod
    def create(cls, fileobj, dest):
        """
        Substantialize $fileobj on dest dynamically.
        
        The contents of the file to generate, is given in fileojb as
        fileobj.content, and if fileobj.content is encoded, it will be decoded
        with using fileobj.decode.

        @fileobj    FileObjects instance
        @dest  str  Destination path to copy to
        """
        assert fileobj.create, "fileobj.create must not be False if you want create it!"

        if not fileobj.get("content", False):
            fileobj.content = fetch(fileobj.src)

        decode = fileobj.get("decode", __id)
        content = decode(fileobj.content)

        open(dest, "w").write(content)

    @classmethod
    def copy_impl(cls, fileobj, dest):
        """
        Copy the file of fileobj to dest.
        
        Two steps needed to keep the content and metadata of the original file:

        1. Copy itself and its some metadata (owner, mode, etc.)
        2. Copy extra metadata not copyable with the above.

        "cp -a" (cp in GNU coreutils) does the above operations at once and
        might be suited for most cases, I think.

        @fileobj    FileObjects instance
        @dest  str  Destination path to copy to
        """
        run("cp -a %s %s" % (fileobj.src, dest))

    @classmethod
    def copy(cls, fileobj, dest, force=False):
        """
        Copy fileobj to $dest. "Copy" action varys depends on actual filetype so that
        inherited class should overrride this and/or related methods.

        @fileobj     FileObjects instance
        @dest  str   The destination path to copy to
        @force bool  When True, it will force overwrite $dest even if it exists
        """
        create_instead_of_copy = fileobj.create

        if not create_instead_of_copy:
            assert fileobj.path != dest, "Copying src and dst are same!"

            if not fileobj.copyable():
                logging.warn(" Not copyable: %s" % str(fileobj))
                return False

        if os.path.exists(dest):
            logging.warn(" Destination already exists: " + dest)

            if force:
                logging.info(" Removing old one in advance: " + dest)
                cls.remove(dest)
            else:
                logging.warn(" Do not overwrite and skip it: " + dest)
                return False
        else:
            destdir = os.path.dirname(dest)

            if not os.path.exists(destdir):
                os.makedirs(destdir)

            if not create_instead_of_copy:
                try:
                    srcdir = os.path.dirname(fileobj.path)
                    shutil.copystat(srcdir, destdir)
                except OSError:
                    logging.warn("Could not copy the stat: " + srcdir)

        if create_instead_of_copy:
            logging.debug(" Creating: " + dest)
            cls.create(fileobj, dest)
        else:
            logging.debug(" Copying: from=%s, to=%s" % (fileobj.path, dest))
            cls.copy_impl(fileobj, dest)

        return True


class DirOps(FileOps):

    @classmethod
    def remove(cls, path):
        assert os.path.isdir(path), "Not a directory! path=" + path
        os.removedirs(path)

    @classmethod
    def create(cls, fileobj, dest):
        try:
            mode = int(fileobj.permission(), 8)  # in octal, e.g. 0755
            os.makedirs(dest, mode)

        except OSError, e:   # It may be OK, ex. non-root user cannot set perms.
            logging.debug(
                " Failed (may be ignorable): os.makedirs, dest=%s, mode=%o" % \
                    (dest, mode)
            )
            logging.warn(e)
            logging.info(" Skipped: " + dest)

            if not os.path.exists(dest):
                run("mkdir -p " + dest)

        uid = os.getuid()
        gid = os.getgid()

        if uid == 0 or (uid == fileobj.uid and gid == fileobj.gid):
            os.chown(dest, fileobj.uid, fileobj.gid)
        else:
            logging.debug("Chown is not permitted so do nothing.")

    @classmethod
    def copy_impl(cls, fileobj, dest):
        cls.create(fileobj, dest)

        try:
            shutil.copystat(fileobj.path, dest)
        except OSError, e:
            logging.warn(str(e))


class SymlinkOps(FileOps):

    link_instead_of_copy = False

    @classmethod
    def create(cls, fileobj, dest):
        os.symlink(fileobj.linkto, dest)

    @classmethod
    def copy_impl(cls, fileobj, dest):
        if cls.link_instead_of_copy:
            cls.create(fileobj, dest)
        else:
            run("cp -a %s %s" % (fileobj.path, dest))


# vim:sw=4 ts=4 et:
