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
from pmaker.globals import PKG_FORMAT_TGZ, PKG_FORMAT_RPM, PKG_FORMAT_RPM, \
    BUILD_STEPS, STEP_PRECONFIGURE, STEP_SETUP, STEP_BUILD, COLLECTORS, \
    TEMPLATE_SEARCH_PATHS, COMPRESSING_TOOLS
from pmaker.utils import memoize, singleton
from pmaker.models.Bunch import Bunch

import pmaker.collectors.Collectors as C
import pmaker.backend.registry as BR

import glob
import logging
import os
import os.path
import platform
import re
import socket
import subprocess


try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        logging.warn(" JSON module is not available. Disabled its support.")
        json = None

try:
    import yaml
except ImportError:
    logging.warn(" YAML module is not available. Disabled its support.")
    yaml = None


try:
    from Cheetah.Template import Template
    UPTO = STEP_BUILD
    CHEETAH_ENABLED = True

except ImportError:
    UPTO = STEP_SETUP
    CHEETAH_ENABLED = False

    logging.warn(
        " python-cheetah is not found. It will go up to the step: " + UPTO
    )


DIST_NAMES = (DIST_RHEL, DIST_FEDORA, DIST_DEBIAN) = \
    ("rhel", "fedora", "debian")


@memoize
def hostname():
    return socket.gethostname() or os.uname()[1]


@memoize
def get_arch():
    """Returns "normalized" architecutre this host can support.
    """
    ia32_re = re.compile(r"i.86")  # i386, i686, etc.

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

    arch = get_arch()

    if os.path.exists(fedora_f):
        name = DIST_FEDORA
        m = re.match(r"^Fedora .+ ([0-9]+) .+$", open(fedora_f).read())
        version = m is None and "14" or m.groups()[0]

    elif os.path.exists(rhel_f):
        name = DIST_RHEL
        m = re.match(r"^Red Hat.* ([0-9]+) .*$", open(fedora_f).read())
        version = m is None and "6" or m.groups()[0]

    elif os.path.exists(debian_f):
        name = DIST_DEBIAN
        m = re.match(r"^([0-9])\..*", open(debian_f).read())
        version = m is None and "6" or m.groups()[0]

    else:
        raise RuntimeError("Not supported distribution!")

    return (name, version, arch)


@memoize
def get_package_format():
    (dist, _v, _a) = get_distribution()

    if dist in (DIST_RHEL, DIST_FEDORA):
        return PKG_FORMAT_RPM
    elif dist in (DIST_DEBIAN):
        return PKG_FORMAT_DEB
    else:
        return PKG_FORMAT_TGZ


@memoize
def get_package_formats():
    (dist, _v, _a) = get_distribution()

    if dist in (DIST_RHEL, DIST_FEDORA):
        return (PKG_FORMAT_TGZ, PKG_FORMAT_RPM)
    elif dist in (DIST_DEBIAN):
        return (PKG_FORMAT_TGZ, PKG_FORMAT_DEB, PKG_FORMAT_RPM)
    else:
        return (PKG_FORMAT_TGZ, )


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
            email = subprocess.check_output(
                "git config --get user.email 2>/dev/null", shell=True
            )
            return email.rstrip()
        except Exception, e:
            logging.warn("get_email: " + str(e))
            pass

    return os.environ.get("MAIL_ADDRESS", False) or \
        "%s@localhost.localdomain" % get_username()


@memoize
def get_fullname():
    """Get full name of the user.
    """
    if is_git_available():
        try:
            fullname = subprocess.check_output(
                "git config --get user.name 2>/dev/null", shell=True
            )
            return fullname.rstrip()
        except Exception, e:
            logging.warn("get_fullname: " + str(e))
            pass

    return os.environ.get("FULLNAME", False) or get_username()


@memoize
def get_compressor(ctools=COMPRESSING_TOOLS):
    global UPTO, CHEETAH_ENABLED

    am_dir_pattern = "/usr/share/automake-*"
    am_files_pattern = am_dir_pattern + "/am/*.am"

    if len(glob.glob(am_dir_pattern)) == 0:  # automake is not installed.
        if CHEETAH_ENABLED:
            UPTO = STEP_PRECONFIGURE
        else:
            UPTO = STEP_SETUP

        logging.warn(
            "Automake not found. The process will go up to the step: " + UPTO
        )

        return ctools[-1]  # fallback to the default (gzip).

    for ct in ctools:
        # NOTE: bzip2 tries compressing input from stdin even it is invoked
        # with --version option. So give null input (/dev/null) to it.
        c_exists = 0 == subprocess.check_call(
            "%(command)s --version > /dev/null 2> /dev/null < /dev/null" % ct,
            shell=True,
        )

        if c_exists:
            am_support_c = 0 == subprocess.check_call(
                "grep -q -e '^dist-%s:' %s 2> /dev/null" % \
                    (ct.command, am_files_pattern),
                shell=True,
            )
            if am_support_c:
                return ct

    # gzip must exist at least and not reached here:
    raise RuntimeError("No compressor found! Aborting...")


@singleton
class Env(Bunch):
    """

    >>> env1 = Env()
    >>> env2 = Env()
    >>> env1 == env2
    """

    def __init__(self, **kwargs):
        global UPTO, BUILD_STEPS, CHEETAH_ENABLED, COMPRESSING_TOOLS, \
            json, yaml

        # from globals
        self.upto = UPTO
        self.build_steps = BUILD_STEPS
        self.cheetah_enabled = CHEETAH_ENABLED
        self.template_paths = TEMPLATE_SEARCH_PATHS

        self.hostname = hostname()
        self.arch = get_arch()
        self.format = get_package_format()
        self.formats = get_package_formats()
        self.is_git_available = is_git_available()
        self.username = get_username()
        self.email = get_email()
        self.fullname = get_fullname()

        n, v, a = get_distribution()
        self.dist = Bunch()
        self.dist.name = n
        self.dist.version = v
        self.dist.arch = a
        self.dist.label = "-".join((n, v, a))

        self.compressor = get_compressor()
        self.compressor.triple = (
            self.compressor.command,
            self.compressor.extension,
            self.compressor.am_option,
        )
        self.compressors = COMPRESSING_TOOLS

        # other complex defaults:
        self.drivers = BR.map()  # {backend_type: backend_class}
        self.driver = BR.default()  # e.g. "autotools.single.rpm"

        self.input_types = C.map()  # {collector_type: collector_class}
        self.input_type = C.default()  # e.g. "filelist"

        self.workdir = os.path.join(os.getcwd(), "workdir")

        # modules
        self.json = json
        self.yaml = yaml

        for k, v in kwargs.iteritems():
            if k not in self:
                self[k] = v


# vim:sw=4 ts=4 et:
