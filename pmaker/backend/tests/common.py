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
from pmaker.tests.common import PATHS

import pmaker.backend.autotools.single.tgz as T
import pmaker.options as O
import pmaker.pkgdata as P
import pmaker.collectors.FilelistCollectors as Collectors

import os.path
import shlex


def dump_filelist(workdir, paths=PATHS):
    output = os.path.join(workdir, "files.list")  # filelist.simple
    open(output, "w").write("\n".join(paths))

    return output


def init_pkgdata(args):
    """
    Initialize PkgData instance passed to backend classes.

    see also pmaker/app.py
    """
    o = O.Options()
    (opts, args) = o.parse_args(shlex.split(args))

    listfile = args[0] if args else opts.config

    ccls = Collectors.map().get(opts.input_type)
    collector = ccls(listfile, opts)

    fs = collector.collect()
    assert fs, "Failed to collect files from " + listfile

    pkgdata = P.PkgData(opts, fs)

    return pkgdata


def try_run(backend):
    try:
        backend.run()
    except SystemExit:
        pass


# vim:sw=4 ts=4 et:
