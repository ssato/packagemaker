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
import pmaker.rpmutils as R
import pmaker.utils as U

import logging
import os.path


def on_debug_mode():
    return U.on_debug_mode()


class Backend(B.Base):

    _format = "rpm"
    _relations = R.RPM_RELATIONS

    def build_srpm(self):
        cmd = "make srpm"

        if not on_debug_mode:
            cmd += " V=0 > " + self.logfile("make_srpm")

        return self.shell(cmd)

    def build_rpm(self):
        use_mock = not self.pkgdata.no_mock

        if use_mock:
            try:
                self.shell("mock --version > /dev/null")

            except RuntimeError, e:
                logging.warn(
                    "Mock is not found. Fallback to plain rpmbuild..."
                )
                use_mock = False

        if use_mock:
            dist = self.pkgdata.dist
            srpm = R.srcrpm_name_by_rpmspec(
                os.path.join(self.workdir, self.pkgdata.name + ".spec")
            )
            cmd = "mock -r %s %s" % (dist, srpm)

            if not on_debug_mode:
                cmd += " --quiet"

            self.shell(cmd)
            print "  GEN    rpm"  # mimics the message of "make rpm"

            return self.shell(
                "mv /var/lib/mock/%s/result/*.rpm %s" % (dist, self.workdir)
            )
        else:
            cmd = "make rpm"

            if not on_debug_mode:
                cmd += " rpm V=0 > " + self.logfile("make_rpm")

            return self.shell(cmd)

    def sbuild(self):
        super(Backend, self).sbuild()
        self.build_srpm()

    def build(self):
        super(Backend, self).build()
        self.build_rpm()


# vim:sw=4 ts=4 et:
