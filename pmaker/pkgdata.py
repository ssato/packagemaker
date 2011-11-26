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
from pmaker.globals import CONFLICTS_NEWDIR, CONFLICTS_SAVEDIR, \
    COMPRESSING_TOOLS, DATE_FMT_RFC2822, DATE_FMT_SIMPLE
from pmaker.models.Bunch import Bunch

import pmaker.utils as U

import datetime
import locale
import logging
import os.path


def __date(type=None):
    """
    TODO: how to output in rfc2822 format w/o email.Utils.formatdate?
    ("%z" for strftime does not look working.)
    """
    locale.setlocale(locale.LC_TIME, "C")

    if type == DATE_FMT_RFC2822:
        fmt = "%a, %d %b %Y %T +0000"

    elif type == DATE_FMT_SIMPLE:
        fmt = "%Y%m%d"

    else:
        fmt = "%a %b %_d %Y"

    return datetime.datetime.now().strftime(fmt)


def date_params():
    return Bunch(date=__date(DATE_FMT_RFC2822), timestamp=__date())


def compressor_params(extopt, ctools=COMPRESSING_TOOLS):
    ct = [ct for ct in ctools if ct.extension == extopt][0]
    return Bunch(ext=extopt, am_opt=ct.am_option)


class PkgData(object):

    def __init__(self, data, files):
        """
        :param data: Package data (parameters) came from command line options
                     and parameter settings in configuration files, to
                     instantiate templates.

                     see also: pmaker/configurations.py, pmaker/options.py
        :param files: List of files (FileObject instances) :: [FileObject]
        """
        keys = (
            "force", "verbosity", "workdir", "stepto", "driver",
            "format", "destdir", "name", "group", "license", "url",
            "summary", "arch", "relations", "packager", "email",
            "pversion", "release", "changelog", "dist",
        )

        for key in keys:
            val = getattr(data, key, None)
            if val is not None:
                setattr(self, key, val)

        self.date = date_params()
        self.compressor = compressor_params(data.compressor)
        self.srcdir = os.path.join(self.workdir, "src")

        self.setup_files(files)

    def setup_files(self, files):
        self.files = files
        self.conflicts = Bunch(
            savedir=CONFLICTS_SAVEDIR % {"name": self.name},
            newdir=CONFLICTS_NEWDIR % {"name": self.name},
            files=[f for f in files if "conflicts" in f],
        )

        self.not_conflicts = Bunch(
            files=[f for f in files if f not in self.conflicts.files],
        )

        self.distdata = U.sort_out_paths_by_dir(
            f.install_path for f in files if f.isfile()
        )


# vim:sw=4 ts=4 et:
