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
class Target(object):

    def __init__(self, path, attrs={}):
        self.path = path
        self.attrs = []

        for attr, val in attrs.iteritems():
            if attr == "path":
                continue

            setattr(self, attr, val)
            self.attrs.append(attr)

    def __cmp__(self, other):
        return cmp(self.path, other.path)

    def attrs(self):
        return self.attrs

    def path(self):
        return path


# vim: set sw=4 ts=4 expandtab:
