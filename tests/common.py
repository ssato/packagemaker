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
import pmaker.tests.common as C

import glob
import logging
import os.path
import random
import subprocess


def setup(extra_args=[]):
    workdir = C.setup_workdir()
    tmpldir = os.path.join(C.TOPDIR, "templates")

    args = [
        "-w", workdir,
        "-P", tmpldir,
    ] + extra_args

    #logging.getLogger().setLevel(logging.WARN) # suppress log messages

    return (workdir, args)


def run_w_args(args, workdir):
    c = [os.path.join(C.TOPDIR, "tools/pmaker")] + args
    cs = " ".join(c)

    e = os.environ
    e["PYTHONPATH"] = C.TOPDIR

    with open(os.path.join(workdir, "test.log"), "w") as f:
        #print "run command: " + cs
        rc = subprocess.call(cs, shell=True, stdout=f, stderr=f, env=e)

    return rc


def get_random_system_files(n=1, pattern="/etc/*"):
    if n == 1:
        return random.choice(
            [f for f in glob.glob(pattern) if os.path.isfile(f)]
        )
    else:
        return random.sample(
            [f for f in glob.glob(pattern) if os.path.isfile(f)], n
        )


# vim:sw=4 ts=4 et:
