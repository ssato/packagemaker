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
from pmaker.globals import STEP_SETUP, STEP_PRECONFIGURE, STEP_CONFIGURE, \
    STEP_SBUILD, STEP_BUILD
from pmaker.tests.common import setup_workdir, cleanup_workdir, TOPDIR

import pmaker.backend.tests.common as TC
import pmaker.backend.registry as Registry

import logging
import os
import os.path
import unittest


def setup():
    logging.getLogger().setLevel(logging.WARN)  # suppress log messages

    workdir = setup_workdir()
    listfile = TC.dump_filelist(workdir)

    return (workdir, listfile)


def get_backend_obj(workdir, listfile, step="build", format="tgz"):
    tmplpath = os.path.join(TOPDIR, "templates")

    btype = "buildrpm.%s" % format

    args = "-n foo -w %s --template-path %s -v" % (workdir, tmplpath)
    args += " --driver %s --stepto %s %s" % (btype, step, listfile)

    pkgdata = TC.init_pkgdata(args)

    bcls = Registry.map().get(btype)
    backend = bcls(pkgdata)

    return backend


def try_run(ut, step, format="tgz"):
    backend = get_backend_obj(ut.workdir, ut.listfile, step, format)
    TC.try_run(backend)

    ut.assertTrue(os.path.exists(backend.marker_path({"name": step})))

    return backend


# vim:sw=4:ts=4:et:
