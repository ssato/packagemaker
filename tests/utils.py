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
from pmaker.cui import main as cui_main
from pmaker.environ import get_compressor

import glob
import os
import os.path
import random
import sys
import tempfile
import unittest


PKG_0 = dict(
    name="foobar",
    version="0.0.1",
    release="1",
)


def helper_create_tmpdir(dir="/tmp", prefix="pmaker-system-tests-"):
    return tempfile.mkdtemp(dir=dir, prefix=prefix)


def helper_is_deb_based_system():
    if os.path.exists("/etc/debian_version"):
        return True
    else:
        print >> sys.stderr, "This system does not look a Deb-based system."
        return False


def helper_is_rpm_based_system():
    if os.path.exists("/var/lib/rpm"):
        return True
    else:
        print >> sys.stderr, "This system does not look a RPM-based system."
        return False


def helper_get_compressor_ext():
    return get_compressor()[1]


def helper_run_with_args(args):
    try:
        cui_main(["dummy_argv_0"] + args.split())
    except SystemExit:
        pass


def helper_random_system_files(num=1):
    if num == 1:
        return random.choice([f for f in glob.glob("/etc/*") if os.path.isfile(f)])
    else:
        return random.sample([f for f in glob.glob("/etc/*") if os.path.isfile(f)], num)


# vim: set sw=4 ts=4 expandtab:
