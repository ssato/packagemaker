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
from pmaker.globals import PMAKER_TEMPLATE_VERSION as TVER

import pmaker.backend.base as B
import pmaker.utils as U
import os.path


class Backend(B.Base):

    _format = "tgz"
    _strategy = "buildrpm"

    _templates = [
        (TVER + "/common/README", "README"),
        (TVER + "/buildrpm/Makefile", "Makefile"),
        (TVER + "/common/apply-overrides", "apply-overrides"),
        (TVER + "/common/revert-overrides", "revert-overrides"),
    ]

    def sbuild(self):
        c = "make dist"
        if not U.on_debug_mode():
            c += " > %s 2> %s" % \
                (self.logfile("sbuild"), self.logfile("sbuild.errors"))

        self.shell(c, timeout=180)


# vim:sw=4 ts=4 et:
