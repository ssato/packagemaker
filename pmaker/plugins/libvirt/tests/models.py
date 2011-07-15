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
from pmaker.plugins.libvirt.models import *
from pmaker.utils import rm_rf
from pmaker.shell import shell

import doctest
import os.path
import tempfile
import unittest



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


TEST_NETWORK_XML_0 = """\
<network>
  <name>net-0</name>
  <forward mode='nat'/>
  <bridge name='virbr1' stp='on' delay='0' />
  <domain name='net-1.local'/>
  <ip address='192.168.151.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.151.200' end='192.168.151.254' />
      <host mac='54:52:00:01:00:10' name='service-0' ip='192.168.151.10' />
      <host mac='54:52:00:01:00:11' name='service-1' ip='192.168.151.11' />
    </dhcp>
  </ip>
</network>
"""



class TestLibvirtNetwork(unittest.TestCase):

    _multiprocess_shared_ = True

    def setUp(self):
        global TEST_NETWORK_XML_0

        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pplx-")

        xmlpath = os.path.join(self.workdir, "net-0.xml")
        open(xmlpath, "w").write(TEST_NETWORK_XML_0)

        self.xmlpath = xmlpath

    def tearDown(self):
        rm_rf(self.workdir)

    def test_instance_by_xmlpath(self):
        lnet = LibvirtNetwork(xmlpath=self.xmlpath)

        self.assertEquals(lnet.name, "net-0")

    def test_instance_by_name(self):
        lnet = LibvirtNetwork("net-0")

        self.assertEquals(lnet.xmlpath, LibvirtNetwork.xmlpath_fmt % (lnet.type, lnet.name))



class TestLibvirtDomain(unittest.TestCase):

    _multiprocess_shared_ = True

    def setUp(self):
        global TEST_DOMAIN_XML_0

        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pplx-")

        xmlpath = os.path.join(self.workdir, "rhel-5-5-vm-1.xml")
        open(xmlpath, "w").write(
            TEST_DOMAIN_XML_0.replace("/var/lib/libvirt/images/rhel-5-5-guest-1", self.workdir)
        )

        bimg0 = os.path.join(self.workdir, "disk-0-base.img")
        bimg1 = os.path.join(self.workdir, "disk-1-base.img")
        img0 = os.path.join(self.workdir, "disk-0.qcow2")
        img1 = os.path.join(self.workdir, "disk-1.qcow2")

        shell("qemu-img create -f qcow2 %s 1G" % bimg0, self.workdir)
        shell("qemu-img create -f qcow2 %s 1G" % bimg1, self.workdir)

        shell("qemu-img create -f qcow2 -b %s %s" % (bimg0, img0), self.workdir)
        shell("qemu-img create -f qcow2 -b %s %s" % (bimg1, img1), self.workdir)

        self.xmlpath = xmlpath
        self.base_images = [bimg0, bimg1]
        self.delta_images = [img0, img1]

        self.xmlpath = xmlpath

    def tearDown(self):
        rm_rf(self.workdir)

    def test_instance_by_xmlpath(self):
        domain = LibvirtDomain(xmlpath=self.xmlpath)

        self.assertEquals(domain.name, "rhel-5-5-vm-1")
        self.assertEquals(domain.arch, "i686")
        self.assertListEqual(domain.networks, ["net-1", "net-2"])

        self.assertListEqual(domain.base_images, self.base_images)
        self.assertListEqual(domain.delta_images, self.delta_images)


# vim:sw=4:ts=4:et:
