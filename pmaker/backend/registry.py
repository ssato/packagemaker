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
import pmaker.backend.autotools.single.tgz
import pmaker.backend.autotools.single.rpm
import pmaker.backend.autotools.single.deb


def map():
    backends = [
        pmaker.backend.autotools.single.tgz.Backend,
        pmaker.backend.autotools.single.rpm.Backend,
        pmaker.backend.autotools.single.deb.Backend,
    ]

    return dict((b.type(), b) for b in backends)


def default():
    return pmaker.backend.autotools.single.rpm.Backend.type()


# vim:sw=4 ts=4 et:
