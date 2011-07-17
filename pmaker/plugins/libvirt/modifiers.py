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
from pmaker.collectors.Modifiers import FileInfoModifier

import logging
import os.path



class LibvirtObjectXMLModifier(FileInfoModifier):

    _priority = 7

    def __init__(self, obj):
        self.obj = obj

    def update(self, fileinfo, *args, **kwargs):
        if fileinfo.path.endswith(".xml"):  # it should be obj xml
            if getattr(fileinfo, "target", False):
                fileinfo.target = fileinfo.target.replace(os.path.dirname(fileinfo.path), self.obj.xmlsavedir)
            else:
                fileinfo.target = os.path.join(self.obj.xmlsavedir, "%s.xml" % self.obj.name)

        return fileinfo


# vim: set sw=4 ts=4 expandtab:
