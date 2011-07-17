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
from pmaker.plugins.libvirt.modifiers import *
from pmaker.utils import unique

import libvirt
import logging
import os
import re
import subprocess



class RpmLibvirtDomainPackageMaker(AutotoolsRpmPackageMaker):

    def __init__(self, package, domname, options, *args, **kwargs):
        """
        $filelist (FILELIST) parameter is interpreted as a domain name.
        """
        super(LibvirtDomainCollector, self).__init__(package, domname, options)
        self._templates["%s.spec" % self.pname] = "libvirt/domain/package.spec"
    
        self.domain = LibvirtDomain(self.filelist)  # filelist == domain name
        self.package["domain"] = self.domain




class DebLibvirtDomainPackageMaker(pmaker.DebPackageMaker):

    global LIBVIRT_DOMAIN_TEMPLATES

    _templates = LIBVIRT_DOMAIN_TEMPLATES
    _type = "libvirt.domain"
    _collector = LibvirtDomainCollector

    def __init__(self, package, domname, options, *args, **kwargs):
        super(LibvirtDomainCollector, self).__init__(package, domname, options)

        self.domain = LibvirtDomain(self.filelist)
        self.package["domain"] = LibvirtDomain(domname)


# vim:sw=4:ts=4:et:
