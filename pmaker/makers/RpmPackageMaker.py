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
from pmaker.globals import *
from pmaker.rpm import *
from pmaker.utils import *

import logging
import os
import os.path
import re
import sys



class RpmPackageMaker(TgzPackageMaker):
    _format = "rpm"

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

    def rpmspec(self):
        return os.path.join(self.workdir, "%s.spec" % self.pname)

    def build_srpm(self):
        if on_debug_mode:
            return self.shell("make srpm")
        else:
            return self.shell("make srpm V=0 > /dev/null")

    def build_rpm(self):
        use_mock = not self.options.no_mock

        if use_mock:
            try:
                self.shell("mock --version > /dev/null")
            except RuntimeError, e:
                logging.warn(" It seems mock is not found on your system. Fallback to plain rpmbuild...")
                use_mock = False

        if use_mock:
            silent = (on_debug_mode() and "" or "--quiet")
            self.shell("mock -r %s %s %s" % \
                (self.package["dist"], srcrpm_name_by_rpmspec(self.rpmspec()), silent)
            )
            print "  GEN    rpm"  # mimics the message of "make rpm"
            return self.shell("mv /var/lib/mock/%(dist)s/result/*.rpm %(workdir)s" % self.package)
        else:
            if on_debug_mode:
                return self.shell("make rpm")
            else:
                return self.shell("make rpm V=0 > /dev/null")

    def preconfigure(self):
        super(RpmPackageMaker, self).preconfigure()

        self.genfile("rpm.mk")
        self.genfile("package.spec", "%s.spec" % self.pname)

    def sbuild(self):
        super(RpmPackageMaker, self).sbuild()

        self.build_srpm()

    def build(self):
        super(RpmPackageMaker, self).build()

        self.build_rpm()



class DebPackageMaker(TgzPackageMaker):
    _format = "deb"

    # TODO: Add almost relation tag set:
    _relations = {
        "requires": "Depends",
    }

    def preconfigure(self):
        super(DebPackageMaker, self).preconfigure()

        debiandir = os.path.join(self.workdir, "debian")

        if not os.path.exists(debiandir):
            os.makedirs(debiandir, 0755)

        os.makedirs(os.path.join(debiandir, "source"), 0755)

        self.genfile("debian/rules")
        self.genfile("debian/control")
        self.genfile("debian/copyright")
        self.genfile("debian/changelog")
        self.genfile("debian/dirs")
        self.genfile("debian/compat")
        self.genfile("debian/source/format")
        self.genfile("debian/source/options")

        os.chmod(os.path.join(self.workdir, "debian/rules"), 0755)

    def sbuild(self):
        """FIXME: What should be done for building source packages?
        """
        super(DebPackageMaker, self).sbuild()
        self.shell("dpkg-buildpackage -S")

    def build(self):
        """Which is better to build?

        * debuild -us -uc
        * fakeroot debian/rules binary
        """
        super(DebPackageMaker, self).build()
        self.shell("fakeroot debian/rules binary")



RpmPackageMaker.register()
DebPackageMaker.register()

# vim: set sw=4 ts=4 expandtab:
