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
import pmaker.backend.AutotoolsSingleTgz as A
import pmaker.rpmutils as R
import pmaker.utils as U

import logging
import os.path


class AutotoolsSingleRpm(A.AutotoolsSingleTgz):
    """Rpm support.
    """

    _format = "rpm"

    # FIXME: Fix naming convention of relation keys.
    _relations = {
        "requires": "Requires",
        "requires.pre": "Requires(pre)",
        "requires.preun": "Requires(preun)",
        "requires.post": "Requires(post)",
        "requires.postun": "Requires(postun)",
        "requires.verify": "Requires(verify)",
        "conflicts": "Conflicts",
        "provides": "Provides",
        "obsoletes": "Obsoletes",
    }

    # Initialize this in __init__ method:
    #_templates = ...

    def __init__(self, package, **kwargs):
        super(AutotoolsSingleRpm, self).__init__(package, **kwargs)

        self._templates += [
            ("autotools/rpm.mk", "rpm.mk"),
            ("autotools.single/package.spec", self.package.name + ".spec"),
        ]

        self.on_debug_mode = U.on_debug_mode()

    def __build_srpm(self):
        cmd = "make srpm"

        if not self.on_debug_mode:
            cmd += " V=0 > /dev/null"

        return self.shell(cmd)

    def __build_rpm(self):
        use_mock = not self.package.no_mock

        if use_mock:
            try:
                self.shell("mock --version > /dev/null")

            except RuntimeError, e:
                logging.warn(
                    " Mock is not found. Fallback to plain rpmbuild..."
                )
                use_mock = False

        if use_mock:
            dist = self.package.dist.label
            srpm = R.srcrpm_name_by_rpmspec(
                os.path.join(self.workdir, self.package.name + ".spec")
            )
            cmd = "mock -r %s %s" % (dist, srpm)

            if not self.on_debug_mode:
                cmd += " --quiet"

            self.shell(cmd)
            print "  GEN    rpm"  # mimics the message of "make rpm"

            return self.shell(
                "mv /var/lib/mock/%s/result/*.rpm %s" % (dist, self.workdir)
            )
        else:
            cmd = "make rpm"

            if not self.on_debug_mode:
                cmd += " rpm V=0 > /dev/null"

            return self.shell(cmd)

    def sbuild(self):
        super(AutotoolsSingleRpm, self).sbuild()
        self.__build_srpm()

    def build(self):
        super(AutotoolsSingleRpm, self).build()
        self.__build_rpm()


# vim:sw=4 ts=4 et:
