#
# Copyright (C) 2011 Satoru SATOH <ssato @ redhat.com>
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

import pmaker.backend.buildrpm.tgz as T
import pmaker.backend.rpm as R

import logging
import os.path


class Backend(T.Backend, R.Backend):

    _format = "rpm"

    def __init__(self, pkgdata, **kwargs):
        super(Backend, self).__init__(pkgdata, **kwargs)

        self._templates += [
            (TVER + "/buildrpm/rpm.mk", "rpm.mk"),
            (TVER + "/buildrpm/package.spec", self.pkgdata.name + ".spec"),
        ]

        logging.debug("pkgdata.relations=" + str(self.pkgdata.relations))

    def configure(self):
        pass  # Nothing to do.

    def sbuild(self):
        super(Backend, self).sbuild()
        self.build_srpm()

    def build(self):
        super(Backend, self).build()
        self.build_rpm()


# vim:sw=4:ts=4:et:
