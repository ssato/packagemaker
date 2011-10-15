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
#

# TODO: Keep items' order:
#from collections import OrderedDict as dict


class Bunch(dict):
    """
    Simple class implements 'Bunch Pattern'.

    @see http://ruslanspivak.com/2011/06/12/the-bunch-pattern/
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getstate__(self):
        return self.copy()

    def __setstate__(self, dic):
        self.__dict__ = dic

    def __str__(self):
        """
        Remove special methods and attributes which starts with "__" from
        string representation.
        """
        return str(dict((k, v) for k, v in self.iteritems() if not k.startswith("__")))


# vim:sw=4 ts=4 et:
