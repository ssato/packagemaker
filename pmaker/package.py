#
# Copyright (C) 2011 Satoru SATOH <satoru.satoh @ gmail.com>
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
from pmaker.environ import hostname
from pmaker.models.Bunch import Bunch
from pmaker.utils import sort_out_paths_by_dir

import datetime
import locale
import logging
import os.path


def date(type=None):
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
    return dict(date=date(DATE_FMT_RFC2822), timestamp=date())


def compressor_params(extopt, ctools=COMPRESSING_TOOLS):
    ct = [ct for ct in ctools if ct.extension == extopt][0]
    return dict(ext=extopt, am_opt=ct.am_option)


def load_txt_content(txtpath):
    try:
        return open(txtpath).read()

    except IOError:
        logging.warn(
            " Could not open %s to read content." % txtpath
        )


class Package(object):

    def __init__(self, options):
        """
        @param  package    Dict holding package's metadata
        @param  options    Command line options :: optparse.Option  (FIXME)
        """
        self.fileinfos = self.files = []

        keys = ("workdir", "destdir", "upto", "name", "release", "group",
            "license", "url", "packager", "email", "relations", "dist")

        for key in keys:
            val = getattr(options, key, None)
            if val is not None:
                setattr(self, key, val)

        self.version = options.pversion
        self.noarch = not options.arch
        self.changelog = load_txt_content(options.changelog)
        self.host = hostname()
        self.date = date_params()
        self.compressor = compressor_params(options.compressor)
        self.summary = options.summary or "Custom package of " + options.name

        self.srcdir = os.path.join(self.workdir, "src")

        self.conflicts_savedir = CONFLICTS_SAVEDIR % self.as_dict()
        self.conflicts_newdir = CONFLICTS_NEWDIR % self.as_dict()

        self.conflicts = Bunch(
            savedir=self.conflicts_savedir,
            newdir=self.conflicts_newdir,
        )
        self.not_conflicts = Bunch()

    def add_fileinfos(self, files):
        self.fileinfos = self.files = \
            self.fileinfos + [f for f in files if f not in self.fileinfos]

        self.distdata = sort_out_paths_by_dir(
            f.install_path for f in self.files if f.isfile()
        )
        self.conflicted_fileinfos = [
            f for f in self.files if getattr(f, "conflicts", False)
        ]
        self.not_conflicted_fileinfos = [
            f for f in self.files if not getattr(f, "conflicts", False)
        ]

        self.conflicts.files = self.conflicted_fileinfos
        self.not_conflicts.files = self.not_conflicted_fileinfos

    def update(self, update_dict):
        self.__dict__.update(update_dict)

    def as_dict(self):
        return self.__dict__


# vim:sw=4 ts=4 et:
