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
from pmaker.makers.PackageMaker import TgzPackageMaker

import os
import os.path



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

        self.genfile("common/debian/rules", "debian/rules")
        self.genfile("autotools/debian/control", "debian/control")
        self.genfile("common/debian/copyright", "debian/copyright")
        self.genfile("common/debian/changelog", "debian/changelog")
        self.genfile("common/debian/dirs", "debian/dirs")
        self.genfile("common/debian/compat", "debian/compat")
        self.genfile("common/debian/source/format", "debian/source/format")
        self.genfile("common/debian/source/options", "debian/source/options")

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



DebPackageMaker.register()

# vim: set sw=4 ts=4 expandtab:
