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
#
import pmaker.utils as U

import glob
import os.path
import tempfile


PATHS = [
    "/etc/auto.*",  # glob; will be expanded to path list.
    "#/etc/aliases.db",  # comment; will be ignored.
    "/etc/httpd/conf.d",
    "/etc/httpd/conf.d/*",  # glob
    "/etc/modprobe.d/*",  # glob
    "/etc/rc.d/init.d",  # dir, not file
    "/etc/rc.d/rc",
    "/etc/resolv.conf",
    "/etc/reslv.conf",  # should not exist
    "/etc/grub.conf",  # should not be able to read
    "/usr/share/automake-*/am/*.am",  # glob
    "/var/run/*",  # glob, and some of them should not be able to read
    "/root/*",  # likewise.
]

PATHS_EXPANDED = U.unique(
    U.concat(
        "*" in p and glob.glob(p) or [p] for p in PATHS \
            if not p.startswith("#")
    )
)


def setup_workdir():
    return tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")


def cleanup_workdir(workdir):
    U.rm_rf(workdir)


def selfdir():
    return os.path.dirname(__file__)


TOPDIR = os.path.abspath(os.path.join(selfdir(), "../.."))


# vim:sw=4 ts=4 et:
