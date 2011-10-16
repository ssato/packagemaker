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
from pmaker.backend.AutotoolsSingleTgz import AutotoolsSingleTgz
from pmaker.backend.AutotoolsSingleRpm import AutotoolsSingleRpm
from pmaker.backend.AutotoolsSingleDeb import AutotoolsSingleDeb


def map():
    backends = [
        AutotoolsSingleTgz, AutotoolsSingleRpm, AutotoolsSingleDeb,
    ]

    return dict((b.type(), b) for b in backends)


def default():
    return AutotoolsSingleRpm.type()


# vim:sw=4 ts=4 et:
