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
from pmaker.globals import *  # COMPRESSORS, UPTO, CHEETAH_ENABLED
from pmaker.utils import *    # memoize

import glob
import logging
import os
import os.path
import platform
import re
import socket
import subprocess



@memoize
def hostname():
    return socket.gethostname() or os.uname()[1]


@memoize
def get_arch():
    """Returns "normalized" architecutre this host can support.
    """
    ia32_re = re.compile(r"i.86") # i386, i686, etc.

    arch = platform.machine() or "i386"

    if ia32_re.match(arch) is not None:
        return "i386"
    else:
        return arch


@memoize
def get_distribution():
    """Get name and version of the distribution of the system based on
    heuristics.
    """
    fedora_f = "/etc/fedora-release"
    rhel_f = "/etc/redhat-release"
    debian_f = "/etc/debian_version"

    if os.path.exists(fedora_f):
        name = "fedora"
        m = re.match(r"^Fedora .+ ([0-9]+) .+$", open(fedora_f).read())
        version = m is None and "14" or m.groups()[0]

    elif os.path.exists(rhel_f):
        name = "rhel"
        m = re.match(r"^Red Hat.* ([0-9]+) .*$", open(fedora_f).read())
        version = m is None and "6" or m.groups()[0]

    elif os.path.exists(debian_f):
        name = "debian"
        m = re.match(r"^([0-9])\..*", open(debian_f).read())
        version = m is None and "6" or m.groups()[0]

    else:
        raise RuntimeError("Not supported distribution!")

    return (name, version)


@memoize
def is_git_available():
    return os.system("git --version > /dev/null 2> /dev/null") == 0


@memoize
def get_username():
    return os.environ.get("USER", False) or os.getlogin()


@memoize
def get_email():
    if is_git_available():
        try:
            email = subprocess.check_output("git config --get user.email 2>/dev/null", shell=True)
            return email.rstrip()
        except Exception, e:
            logging.warn("get_email: " + str(e))
            pass

    return os.environ.get("MAIL_ADDRESS", False) or "%s@localhost.localdomain" % get_username()


@memoize
def get_fullname():
    """Get full name of the user.
    """
    if is_git_available():
        try:
            fullname = subprocess.check_output("git config --get user.name 2>/dev/null", shell=True)
            return fullname.rstrip()
        except Exception, e:
            logging.warn("get_fullname: " + str(e))
            pass

    return os.environ.get("FULLNAME", False) or get_username()


def get_compressor(compressors=COMPRESSORS):
    global UPTO, CHEETAH_ENABLED

    found = False

    am_dir_pattern = "/usr/share/automake-*"
    am_files_pattern = am_dir_pattern + "/am/*.am"
    
    if len(glob.glob(am_dir_pattern)) == 0:
        UPTO = CHEETAH_ENABLED and STEP_PRECONFIGURE or STEP_SETUP
        logging.warn("Automake not found. The process will go up to the step: " + UPTO)

        return ("gzip",  "gz",  "")  # fallback to the default.

    for cmd, ext, am_opt in compressors:
        # bzip2 tries compressing input from stdin even it
        # is invoked with --version option. So give null input to it.
        cmd_c = "%s --version > /dev/null 2> /dev/null < /dev/null" % cmd

        if os.system(cmd_c) == 0:
            am_support_c = "grep -q -e '^dist-%s:' %s 2> /dev/null" % (cmd, am_files_pattern)

            if os.system(am_support_c) == 0:
                found = True
                break

    if not found:
        #logging.warn("any compressors not found. Packaging process can go up to \"setup\" step.")
        #UPTO = STEP_SETUP
        #return False

        # gzip must exist at least and not reached here:
        raise RuntimeError("No compressor found! Aborting...")

    return (cmd, ext, am_opt)


# vim: set sw=4 ts=4 expandtab:
