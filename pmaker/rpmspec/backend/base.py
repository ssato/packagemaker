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
import pmaker.backend.base as BB
import pmaker.utils as U


class Base(BB.Base):
    """
    Abstract class for children to implement packaging backends.
    """
    _format = "rpm"
    _strategy = None  # packaging strategy, e.g. rpmspec.python

    # Relations between packages :: { relation_key: package_specific_repr }
    _relations = {
        # e.g. "requires": "Requires",
        #      "requires.pre": "Requires(pre)",
        #      "conflicts": "Conflicts",
    }

    def setup(self):
        U.createdir(self.workdir)

    def preconfigure(self):
        for template, output in self._templates:
            self.genfile(template, output)

    def configure(self):
        pass

    def sbuild(self):
        pass

    def build(self):
        pass


# vim:sw=4:ts=4:et:
