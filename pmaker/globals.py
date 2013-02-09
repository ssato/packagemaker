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
import pmaker.models.Bunch as B
import datetime
import logging
import os.path

try:
    from collections import OrderedDict as dict
except ImportError:
    pass


PMAKER_NAME = "pmaker"
PMAKER_TITLE = "packagemaker"
PMAKER_AUTHOR = "Satoru SATOH"
PMAKER_EMAIL = "satoru.satoh@gmail.com"
PMAKER_WEBSITE = "https://github.com/ssato/packagemaker"

PMAKER_VERSION = "0.4.1"
#PMAKER_VERSION += "." + datetime.datetime.now().strftime("%Y%m%d")

PMAKER_TEMPLATE_VERSION = "1"


FILEINFOS = dict()
PACKAGE_MAKERS = dict()
COLLECTORS = dict()
BACKENDS = dict()

TEMPLATE_SEARCH_PATHS = ["/usr/share/pmaker/templates", ]

COMPRESSING_TOOLS = [
    B.Bunch(
        command="xz",
        extension="xz",
        am_option="no-dist-gzip dist-xz"
    ),
    B.Bunch(
        command="bzip2",
        extension="bz2",
        am_option="no-dist-gzip dist-bzip2"
    ),
    B.Bunch(
        command="gzip",
        extension="gz",
        am_option=""
    ),
]

CONFLICTS_STATEDIR = "/var/lib/%(name)s-overrides"
CONFLICTS_SAVEDIR = os.path.join(CONFLICTS_STATEDIR, "saved")
CONFLICTS_NEWDIR = os.path.join(CONFLICTS_STATEDIR, "new")


TYPE_FILE = "file"
TYPE_DIR = "dir"
TYPE_SYMLINK = "symlink"
TYPE_OTHER = "other"
TYPE_UNKNOWN = "unknown"

TYPES_SUPPORTED = (TYPE_FILE, TYPE_DIR, TYPE_SYMLINK)


(DATE_FMT_RFC2822, DATE_FMT_SIMPLE) = (0, 1)


TEST_CHOICES = (TEST_BASIC, TEST_FULL) = ("basic", "full")


STEP_SETUP = "setup"
STEP_PRECONFIGURE = "preconfigure"
STEP_CONFIGURE = "configure"
STEP_SBUILD = "sbuild"
STEP_BUILD = "build"

UPTO = STEP_BUILD

BUILD_STEPS = (
    # step_name, log_msg_fmt, help_txt
    (STEP_SETUP, "Setting up src tree in %(workdir)s: %(pname)s",
        "setup the package' src dir and copy target files in it"),

    (STEP_PRECONFIGURE, "Making up autotool-ized src directory: %(pname)s",
        "arrange build aux files such like configure.ac, Makefile.am, " + \
        "rpm spec file, debian/* and so on."),

    (STEP_CONFIGURE, "Configuring src distribution: %(pname)s",
        "setup src dir to run './configure'. autotools will be needed"),

    (STEP_SBUILD, "Building src package: %(pname)s", "build src package[s]"),

    (STEP_BUILD, "Building bin packages: %(pname)s",
        "build binary package[s]"),
)

PACKAGING_STEPS = [
    B.Bunch(
        name=STEP_SETUP,
        message="Setting up src tree in %(workdir)s: %(name)s",
        help="Setup a src dir to save objects and make package",
    ),
    B.Bunch(
        name=STEP_PRECONFIGURE,
        message="Preparing aux files in %(workdir)s: %(name)s",
        help="""\
Preparing build aux files such like configure.ac, rpm spec, etc.""",
    ),
    B.Bunch(
        name=STEP_CONFIGURE,
        message="Configuring build aux files: %(name)s",
        help="""\
Configure build aux files such as configure and Makefile.
Tools like autoconf may be needed depends on drivers""",
    ),
    B.Bunch(
        name=STEP_SBUILD,
        message="Building source package: %(name)s",
        help="Build source package[s]",
    ),
    B.Bunch(
        name=STEP_BUILD,
        message="Building binary package[s]: %(name)s",
        help="Build binary package[s]",
    ),
]


JSON_ENABLED = False


try:
    import json
    JSON_ENABLED = True

except ImportError:
    try:
        import simplejson as json
        JSON_ENABLED = True

    except ImportError:
        logging.warn(
            "json module is not found. JSON support will be disabled."
        )


PKG_FORMATS = (PKG_FORMAT_TGZ, PKG_FORMAT_RPM, PKG_FORMAT_DEB) = \
    ("tgz", "rpm", "deb")


# vim:sw=4:ts=4:et:
