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
from pmaker.tests.common import setup_workdir, cleanup_workdir

import pmaker.models.FileObjects as FO
import pmaker.models.FileObjectFactory as Factory

import os
import unittest


def modestr_to_mode(mode):
    """
    >>> modestr_to_mode("0644")
    420
    >>> oct(modestr_to_mode("0644")) 
    '0644'
    """
    return int(mode, 8)


class Test__guess_filetype(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

        self.file = os.path.join(self.workdir, "file.txt")
        open(self.file, "w").write("This is a file")

        self.dir = os.path.join(self.workdir, "dir")
        os.makedirs(self.dir)

        self.symlink = os.path.join(self.workdir, "test.symlink")
        os.symlink(self.file, self.symlink)

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test__file_dir_and_symlink(self):
        st_mode = Factory.lstat(self.file)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), TYPE_FILE)

        st_mode = Factory.lstat(self.dir)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), TYPE_DIR)

        st_mode = Factory.lstat(self.symlink)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), TYPE_SYMLINK)

    def test__other(self):
        _path = "/dev/null"
        if not os.path.exists(_path):
            logging.warn("%s does not exist. Skip this test." % _path)

        st_mode = Factory.lstat(_path)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), TYPE_OTHER)


class Test__create_from_real_object(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()

        self.file = os.path.join(self.workdir, "file.txt")
        open(self.file, "w").write("This is a file")

        self.file_mode = "0640"
        os.chmod(self.file, modestr_to_mode(self.file_mode))

        self.dir = os.path.join(self.workdir, "dir")
        os.makedirs(self.dir)

        self.dir_mode = "0750"
        os.chmod(self.dir, modestr_to_mode(self.dir_mode))

        self.symlink = os.path.join(self.workdir, "test.symlink")
        os.symlink(self.file, self.symlink)

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test__file_wo_metadata(self):
        fo = FO.XObject(self.file)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.type(), TYPE_FILE)
        self.assertEquals(fo.path, self.file)
        self.assertEquals(fo.mode, self.file_mode)

    def test__dir_wo_metadata(self):
        fo = FO.XObject(self.dir)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.DirObject))
        self.assertEquals(fo.type(), TYPE_DIR)
        self.assertEquals(fo.path, self.dir)
        self.assertEquals(fo.mode, self.dir_mode)

    def test__symlink_wo_metadata(self):
        fo = FO.XObject(self.symlink)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.SymlinkObject))
        self.assertEquals(fo.type(), TYPE_SYMLINK)
        self.assertEquals(fo.path, self.symlink)

    def test__file_w_mode(self):
        mode = "0600"

        fo = FO.XObject(self.file, mode=mode)
        fo = Factory.create_from_real_object(fo)

        self.assertEquals(fo.mode, mode)

    def test__file_w_uid_and_gid(self):
        uid = 1
        gid = 1

        fo = FO.XObject(self.file, uid=uid, gid=gid)
        fo = Factory.create_from_real_object(fo)

        self.assertEquals(fo.uid, uid)
        self.assertEquals(fo.gid, gid)

    def test__dir_w_mode(self):
        mode = "0700"
        fo = FO.XObject(self.dir, mode)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.DirObject))
        self.assertEquals(fo.type(), TYPE_DIR)
        self.assertEquals(fo.path, self.dir)
        self.assertEquals(fo.mode, mode)


class Test__create(unittest.TestCase):

    def setUp(self):
        self.workdir = setup_workdir()
        self.path = os.path.join(self.workdir, "obj_not_exist")

    def tearDown(self):
        cleanup_workdir(self.workdir)

    def test__create_w_filetype_file(self):
        filetype = "file"
        fo = Factory.create(self.path, content="Hello, world")

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.type(), TYPE_FILE)
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.mode, FO.FileObject.defaults.mode)
        self.assertEquals(fo.uid, FO.FileObject.defaults.uid)
        self.assertEquals(fo.gid, FO.FileObject.defaults.gid)
        self.assertEquals(fo.checksum, FO.FileObject.defaults.checksum)


# vim:sw=4 ts=4 et: