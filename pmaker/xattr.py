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
try:
    import xattr as _xa   # pyxattr
    PYXATTR_ENABLED = True

    def get_all(*args):
        return _xa.get_all(*args)

    def set(*args):
        return _xa.set(*args)

except ImportError:
    # Make up a "Null-Object" like class mimics xattr module.
    def get_all(*args):
        return ()

    def set(*args):
        return ()


# vim: set sw=4 ts=4 expandtab:
