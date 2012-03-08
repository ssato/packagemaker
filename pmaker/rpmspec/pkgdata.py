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
import pmaker.models.Bunch as B
import pmaker.utils as U

import logging
import os.path


class PkgData(B.Bunch):

    def __init__(self, data):
        """
        :param data: Package data (parameters) came from command line options
                     and parameter settings in configuration files, to
                     instantiate templates.

                     see also: pmaker/configurations.py, pmaker/options.py
        """
        keys = (
            "force", "verbosity", "workdir", "name", "group", "license", "url",
            "summary", "arch", "relations", "packager", "email", "pversion",
            "release", "dist", "template_paths", "no_mock",
        )

        for key in keys:
            val = getattr(data, key, None)
            if val is not None:
                setattr(self, key, val)


# vim:sw=4 ts=4 et:
