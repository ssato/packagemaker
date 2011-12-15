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
from pmaker.globals import STEP_BUILD
from pmaker.tests.common import PATHS, setup_workdir, TOPDIR

import pmaker.backend.registry as Registry
import pmaker.options as O
import pmaker.pkgdata as P
import pmaker.collectors.FilelistCollectors as Collectors

import logging
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


def setup_workdir_and_listfile():
    logging.getLogger().setLevel(logging.WARN)  # suppress log messages

    workdir = setup_workdir()
    listfile = dump_filelist(workdir)

    return (workdir, listfile)


class BackendTester(object):

    def __init__(self, workdir, listfile, step=STEP_BUILD,
            btype="autotools.single.tgz"):
        """
        Initialize backend object.
        """
        self.workdir = workdir
        self.listfile = listfile
        self.step = step

        tmplpath = os.path.join(TOPDIR, "templates")

        args = "-n foo -w %s --template-path %s -v" % (workdir, tmplpath)
        args += " --driver %s --stepto %s %s" % (btype, step, listfile)

        pkgdata = init_pkgdata(args)

        bcls = Registry.map().get(btype)
        self.backend = bcls(pkgdata)

    def try_run(self):
        try:
            self.backend.run()
        except SystemExit:
            pass

        return os.path.exists(
            self.backend.marker_path({"name": self.step})
        )


# vim:sw=4 ts=4 et:
