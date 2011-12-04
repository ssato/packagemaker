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
from pmaker.utils import rm_rf
from pmaker.tests.common import setup_workdir, TOPDIR
from tests.utils import *

import logging
import os.path
import subprocess


def setup(extra_args=[]):
    workdir = setup_workdir()
    tmpldir = os.path.join(TOPDIR, "templates")

    args = [
        "-n", "foo",
        "-w", workdir,
        "-P", tmpldir,
    ] + extra_args

    logging.getLogger().setLevel(logging.WARN) # suppress log messages

    return (workdir, args)


def run_w_args(args, workdir):
    c = ["python ", os.path.join(TOPDIR, "tools/pmaker"), ] + args

    with open(os.path.join(workdir, "test.log"), "w") as f:
        rc = subprocess.call(c, shell=True, stdout=f, stderr=f)

    return rc


# vim:sw=4 ts=4 et:
