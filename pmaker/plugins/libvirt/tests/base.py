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
from pmaker.plugins.libvirt.base import *
from pmaker.utils import rm_rf
from pmaker.shell import shell

import os
import os.path
import tempfile
import unittest



CURDIR = os.getcwd()


TEST_DOMAIN_XML_0 = """\
<domain type='kvm'>
  <name>rhel-5-5-vm-1</name>
  <os>
    <type arch='i686' machine='pc-0.13'>hvm</type>
    <boot dev='hd'/>
  </os>
  <!-- ... snip ... -->
  <devices>
    <emulator>/usr/bin/qemu-kvm</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none'/>
      <source file='/var/lib/libvirt/images/rhel-5-5-guest-1/disk-0.qcow2'/>
      <target dev='vda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </disk>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none'/>
      <source file='/var/lib/libvirt/images/rhel-5-5-guest-1/disk-1.qcow2'/>
      <target dev='vdb' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </disk>
    <interface type='network'>
      <mac address='54:52:00:01:01:55'/>
      <source network='net-1'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
    <interface type='network'>
      <mac address='54:52:00:03:01:55'/>
      <source network='net-2'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
    </interface>
    <!-- ... snip ... -->
  </devices>
</domain>
"""


class TestXpathEval(unittest.TestCase):

    _multiprocess_shared_ = True

    def setUp(self):
        global TEST_DOMAIN_XML_0

        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pplx-")

        xmlpath = os.path.join(self.workdir, "test-0.xml")
        open(xmlpath, "w").write(TEST_DOMAIN_XML_0)

        self.xmlpath = xmlpath

        self.xpath_archs = "/domain/os/type/@arch"
        self.xpath_networks = "/domain/devices/interface[@type='network']/source/@network"
        self.xpath_images = "/domain/devices/disk[@type='file']/source/@file"

    def tearDown(self):
        rm_rf(self.workdir)

    def test_xpath_eval_xmlfile_archs(self):
        self.assertEquals(xpath_eval(self.xpath_archs, self.xmlpath)[0], "i686")

    def test_xpath_eval_xmlfile_networks(self):
        networks = xpath_eval(self.xpath_networks, self.xmlpath)

        self.assertEquals(networks[0], "net-1")
        self.assertEquals(networks[1], "net-2")

    def test_xpath_eval_xmlfile_images(self):
        images = xpath_eval(self.xpath_images, self.xmlpath)

        self.assertEquals(images[0], "/var/lib/libvirt/images/rhel-5-5-guest-1/disk-0.qcow2")
        self.assertEquals(images[1], "/var/lib/libvirt/images/rhel-5-5-guest-1/disk-1.qcow2")

    def test_xpath_eval_ctx(self):
        ctx = xml_context(self.xmlpath)

        self.assertEquals(xpath_eval(self.xpath_archs, ctx=ctx)[0], "i686")

        networks = xpath_eval(self.xpath_networks, ctx=ctx)

        self.assertEquals(networks[0], "net-1")
        self.assertEquals(networks[1], "net-2")

        images = xpath_eval(self.xpath_images, ctx=ctx)

        self.assertEquals(images[0], "/var/lib/libvirt/images/rhel-5-5-guest-1/disk-0.qcow2")
        self.assertEquals(images[1], "/var/lib/libvirt/images/rhel-5-5-guest-1/disk-1.qcow2")



class Test_get_base_image_path(unittest.TestCase):

    _multiprocess_shared_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pplx-")

    def tearDown(self):
        rm_rf(self.workdir)

    def test_get_base_image_path(self):
        ib_relpath = "test0-base.img"
        i_relpath = "test0.img"

        ib_abspath = os.path.join(self.workdir, ib_relpath)
        i_abspath = os.path.join(self.workdir, i_relpath)

        shell("qemu-img create -f qcow2 %s 10M" % ib_relpath, self.workdir)
        shell("qemu-img create -f qcow2 -b %s %s" % (ib_relpath, i_relpath), self.workdir)

        self.assertEquals(get_base_image_path(i_abspath), ib_abspath)

    def test_get_base_image_path__not_base(self):
        ib_relpath = "test0-base.img"
        ib_abspath = os.path.join(self.workdir, ib_relpath)

        shell("qemu-img create -f qcow2 %s 10M" % ib_abspath, CURDIR)

        self.assertEquals(get_base_image_path(ib_abspath), None)


# vim:sw=4:ts=4:et:
