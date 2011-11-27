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

import itertools
import logging
import os
import os.path
import sys


class AutotoolsSingleTgz(B.Base):

    _format = "tgz"
    _strategy = "autotools.single"

    _templates = [
        (TVER + "/autotools.single/configure.ac", "configure.ac"),
        (TVER + "/autotools.single/Makefile.am", "Makefile.am"),
        (TVER + "/common/README", "README"),
        (TVER + "/common/manifest", "MANIFEST"),
        (TVER + "/common/manifest.overrides", "MANIFEST.overrides"),
        (TVER + "/common/apply-overrides", "apply-overrides"),
        (TVER + "/common/revert-overrides", "revert-overrides"),
    ]

    def preconfigure(self):
        super(AutotoolsSingleTgz, self).preconfigure()

    def configure(self):
        if U.on_debug_mode():
            cmd = "autoreconf -vfi"
        else:
            logfile = os.path.join(self.workdir, "pmaker.configure.log")
            cmd = "autoreconf -fi > " + logfile

        self.shell(cmd, timeout=180)

    def sbuild(self):
        if U.on_debug_mode():
            self.shell("./configure --quiet", timeout=180)
            self.shell("make")
            self.shell("make dist")
        else:
            self.shell(
                "./configure --quiet --enable-silent-rules", timeout=180
            )
            self.shell("make V=0 > /dev/null")
            self.shell("make dist V=0 > /dev/null")


# vim:sw=4 ts=4 et:
