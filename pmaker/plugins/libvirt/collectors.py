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
from pmaker.plugins.libvirt.models import LibvirtDomain
from pmaker.plugins.libvirt.modifiers import LibvirtObjectXMLModifier
from pmaker.collectors.Collectors import FilelistCollector
from pmaker.utils import unique



class LibvirtDomainCollector(FilelistCollector):

    _type = "libvirt.domain"

    def __init__(self, domname, options):
        super(LibvirtDomainCollector, self).__init__(domname, options)

        self.domain = LibvirtDomain(domname)
        self.modifiers.append(LibvirtObjectXMLModifier(self.domain))

    def list_targets(self, domname):
        """Gather files of which the domain $domname owns.
        
        @domname  str  Domain's name [dummy arg]
        """
        filelist = [self.domain.xmlpath] + self.domain.base_images + self.domain.delta_images

        return unique(filelist)


# vim:sw=4:ts=4:et:
