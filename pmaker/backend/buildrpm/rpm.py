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

import pmaker.backend.autotools.single.rpm as AR
import pmaker.backend.buildrpm.tgz as T
import pmaker.rpmutils as R
import pmaker.utils as U

import logging
import os.path


class Backend(T.Backend):
    """
    FIXME: Extract common parts in backend classes:
    (pmaker.backend.{autotools.single,buildrpm}.rpm.Backend
    """

    _format = "rpm"

    _relations = AR.Backend._relations

    def __init__(self, pkgdata, **kwargs):
        super(Backend, self).__init__(pkgdata, **kwargs)

        self._templates += [
            (TVER + "/buildrpm/package.spec", self.pkgdata.name + ".spec"),
        ]

        # Override some members (mimics mixin):
        self.asr = AR.Backend(pkgdata, **kwargs)

        self.on_debug_mode = self.asr.on_debug_mode
        self.pkgdata.relations = self.asr.pkgdata.relations

    def sbuild(self):
        super(Backend, self).sbuild()
        self.asr.build_srpm()

    def build(self):
        super(Backend, self).build()
        self.asr.build_rpm()


# vim:sw=4 ts=4 et:
