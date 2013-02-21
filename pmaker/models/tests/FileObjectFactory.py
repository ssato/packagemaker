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
import pmaker.tests.common as C

import pmaker.rpmutils as R
import pmaker.models.FileObjects as FO
import pmaker.models.FileObjectFactory as Factory

import bunch as B
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


class Test__rpm_lstat(unittest.TestCase):

    def test__bin_sh(self):
        self.assertFalse(Factory.rpm_lstat("/bin/sh") is None)


class Test__guess_filetype(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

        self.file = os.path.join(self.workdir, "file.txt")
        open(self.file, "w").write("This is a file")

        self.dir = os.path.join(self.workdir, "dir")
        os.makedirs(self.dir)

        self.symlink = os.path.join(self.workdir, "test.symlink")
        os.symlink(self.file, self.symlink)

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test__file_dir_and_symlink(self):
        st_mode = Factory.lstat(self.file)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), G.TYPE_FILE)

        st_mode = Factory.lstat(self.dir)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), G.TYPE_DIR)

        st_mode = Factory.lstat(self.symlink)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), G.TYPE_SYMLINK)

    def test__other(self):
        _path = "/dev/null"
        if not os.path.exists(_path):
            logging.warn("%s does not exist. Skip this test." % _path)

        st_mode = Factory.lstat(_path)[0]
        self.assertEquals(Factory.guess_filetype(st_mode), G.TYPE_OTHER)


class Test__create_from_real_object(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

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

        self.missinglink = os.path.join(self.workdir, "test.missinglink")
        os.symlink("/non-existent-file", self.missinglink)

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test__file_wo_metadata(self):
        fo = B.Bunch(path=self.file)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.type(), G.TYPE_FILE)
        self.assertEquals(fo.path, self.file)
        self.assertEquals(fo.mode, self.file_mode)

    def test__dir_wo_metadata(self):
        fo = B.Bunch(path=self.dir)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.DirObject))
        self.assertEquals(fo.type(), G.TYPE_DIR)
        self.assertEquals(fo.path, self.dir)
        self.assertEquals(fo.mode, self.dir_mode)

    def test__symlink_wo_metadata(self):
        fo = B.Bunch(path=self.symlink)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.SymlinkObject))
        self.assertEquals(fo.type(), G.TYPE_SYMLINK)
        self.assertEquals(fo.path, self.symlink)

    def test__symlink_missing(self):
        fo = B.Bunch(path=self.missinglink)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.SymlinkObject))
        self.assertEquals(fo.type(), G.TYPE_SYMLINK)
        self.assertEquals(fo.path, self.missinglink)

    def test__file_w_mode(self):
        mode = "0600"

        fo = B.Bunch(path=self.file, mode=mode)
        fo = Factory.create_from_real_object(fo)

        self.assertEquals(fo.mode, mode)

    def test__file_w_uid_and_gid(self):
        uid = 1
        gid = 1

        fo = B.Bunch(path=self.file, uid=uid, gid=gid)
        fo = Factory.create_from_real_object(fo)

        self.assertEquals(fo.uid, uid)
        self.assertEquals(fo.gid, gid)

    def test__dir_w_mode(self):
        mode = "0700"

        fo = B.Bunch(path=self.dir, mode=mode)
        fo = Factory.create_from_real_object(fo)

        self.assertTrue(isinstance(fo, FO.DirObject))
        self.assertEquals(fo.type(), G.TYPE_DIR)
        self.assertEquals(fo.path, self.dir)
        self.assertEquals(fo.mode, mode)


class Test__create(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()
        self.path = os.path.join(self.workdir, "obj_not_exist")

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test__create_w_filetype_file(self):
        filetype = FO.typestr_to_type("file")
        fo = Factory.create(self.path, filetype=filetype)

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.type(), G.TYPE_FILE)
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.mode, fo.defaults.mode)
        self.assertEquals(fo.uid, fo.defaults.uid)
        self.assertEquals(fo.gid, fo.defaults.gid)
        self.assertEquals(fo.checksum, fo.defaults.checksum)

    def test__create_w_filetype_dir(self):
        filetype = FO.typestr_to_type("dir")
        fo = Factory.create(self.path, filetype=filetype)

        self.assertTrue(isinstance(fo, FO.DirObject))
        self.assertEquals(fo.type(), G.TYPE_DIR)
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.mode, fo.defaults.mode)
        self.assertEquals(fo.uid, fo.defaults.uid)
        self.assertEquals(fo.gid, fo.defaults.gid)
        self.assertEquals(fo.checksum, fo.defaults.checksum)

    def test__create_w_filetype_symlink(self):
        filetype = FO.typestr_to_type("symlink")
        fo = Factory.create(self.path, filetype=filetype)

        self.assertTrue(isinstance(fo, FO.SymlinkObject))
        self.assertEquals(fo.type(), G.TYPE_SYMLINK)
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.mode, fo.defaults.mode)
        self.assertEquals(fo.uid, fo.defaults.uid)
        self.assertEquals(fo.gid, fo.defaults.gid)
        self.assertEquals(fo.checksum, fo.defaults.checksum)

    def test__create_w_content(self):
        content = "Hello, world\n"
        fo = Factory.create(self.path, content=content)

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.mode, fo.defaults.mode)
        self.assertEquals(fo.uid, fo.defaults.uid)
        self.assertEquals(fo.gid, fo.defaults.gid)
        self.assertEquals(fo.checksum, fo.defaults.checksum)
        self.assertEquals(fo.content, content)

    def test__create_w_src(self):
        src = "/etc/hosts"
        fo = Factory.create(self.path, src=src)

        self.assertTrue(isinstance(fo, FO.FileObject))
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.mode, fo.defaults.mode)
        self.assertEquals(fo.uid, fo.defaults.uid)
        self.assertEquals(fo.gid, fo.defaults.gid)
        self.assertEquals(fo.checksum, fo.defaults.checksum)
        self.assertEquals(fo.src, src)

    def test__create_w_linkto(self):
        linkto = "/etc/hosts"
        fo = Factory.create(self.path, linkto=linkto)

        self.assertTrue(isinstance(fo, FO.SymlinkObject))
        self.assertEquals(fo.path, self.path)
        self.assertEquals(fo.mode, fo.defaults.mode)
        self.assertEquals(fo.uid, fo.defaults.uid)
        self.assertEquals(fo.gid, fo.defaults.gid)
        self.assertEquals(fo.checksum, fo.defaults.checksum)
        self.assertEquals(fo.linkto, linkto)

    def test__create_wo_attrs(self):
        fo = Factory.create(self.path)

        self.assertTrue(isinstance(fo, FO.DirObject))
        self.assertEquals(fo.mode, fo.defaults.mode)
        self.assertEquals(fo.uid, fo.defaults.uid)
        self.assertEquals(fo.gid, fo.defaults.gid)
        self.assertEquals(fo.checksum, fo.defaults.checksum)
        self.assertEquals(fo.path, self.path)


# vim:sw=4:ts=4:et:
