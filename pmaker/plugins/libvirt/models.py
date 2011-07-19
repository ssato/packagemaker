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
from pmaker.utils import unique

import libvirt
import logging
import os



LIBVIRT_XML_SAVEDIR = "/var/lib/%(name)s"



class LibvirtObject(object):

    name_xpath = "//name"
    xmlpath_fmt = "/etc/libvirt/%s/%s.xml"

    def __init__(self, name=False, xmlpath=False, vmm=VMM):
        assert name or xmlpath, "Not enough arguments"

        self.vmm = vmm
        self.type = self.type_by_vmm(vmm)

        if name:
            self.name = name
            self.xmlpath = self.xmlpath_by_name(name)
        else:
            self.xmlpath = xmlpath
            self.name = self.name_by_xmlpath(self.name_xpath, xmlpath)

        self.setup()

    def setup(self):
        pass

    def name_by_xmlpath(self, xpath_exp, xmlpath):
        return xpath_eval(xpath_exp, xmlpath)[0]

    def xmlpath_by_name(self, name):
        return self.xmlpath_fmt % (self.type, name)

    def type_by_vmm(self, vmm):
        return vmm.split(":")[0]  # e.g. 'qemu'

    def connect(self):
        return libvirt.openReadOnly(self.vmm)



class LibvirtNetwork(LibvirtObject):

    name_xpath = "/network/name"
    xmlpath_fmt = "/etc/libvirt/%s/networks/%s.xml"
    xmlsavedir = os.path.join(LIBVIRT_XML_SAVEDIR, "network")



class LibvirtDomain(LibvirtObject):

    name_xpath = "/domain/name"
    xmlpath_fmt = "/etc/libvirt/%s/%s.xml"
    xmlsavedir = os.path.join(LIBVIRT_XML_SAVEDIR, "domain")

    def setup(self):
        """Parse domain xml and store various guest profile data.

        TODO: storage pool support
        """
        ctx = xml_context(self.xmlpath)

        self.arch = xpath_eval("/domain/os/type/@arch", ctx=ctx)[0]
        self.networks = unique(xpath_eval('/domain/devices/interface[@type="network"]/source/@network', ctx=ctx))

        images = xpath_eval('/domain/devices/disk[@type="file"]/source/@file', ctx=ctx)

        dbs = [(img, get_base_image_path(img)) for img in images]
        self.base_images = [db[1] for db in dbs if db[1] is not None] + \
            [db[0] for db in dbs if db[1] is None]
        self.delta_images = [db[0] for db in dbs if db[1]]

    def status(self):
        conn = self.connect()

        if conn is None: # libvirtd is not running.
            return libvirt.VIR_DOMAIN_SHUTOFF

        dom = conn.lookupByName(self.name)
        if dom:
            return dom.info()[0]
        else:
            return libvirt.VIR_DOMAIN_NONE

    def is_running(self):
        return self.status() == libvirt.VIR_DOMAIN_RUNNING

    def is_shutoff(self):
        return self.status() == libvirt.VIR_DOMAIN_SHUTOFF



# vim:sw=4:ts=4:et:
