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
        ("autotools.single/configure.ac", "configure.ac"),
        ("autotools.single/Makefile.am", "Makefile.am"),
        ("common/README", "README"),
        ("common/manifest", "MANIFEST"),
        ("common/manifest.overrides", "MANIFEST.overrides"),
        ("common/apply-overrides", "apply-overrides"),
        ("common/revert-overrides", "revert-overrides"),
    ]

    def preconfigure(self):
        super(AutotoolsSingleTgz, self).preconfigure()

        self.package.distdata = U.sort_out_paths_by_dir(
            o.install_path for o in self.package.objects if o.isfile()
        )
        self.package.conflicted_objects = [
            o for o in self.package.objects if "conflicts" in o
        ]
        self.package.not_conflicted_objects = [
            o for o in self.package.objects if "conflicts" not in o
        ]

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
            self.shell("./configure --quiet --enable-silent-rules", timeout=180)
            self.shell("make V=0 > /dev/null")
            self.shell("make dist V=0 > /dev/null")


# vim:sw=4 ts=4 et:
