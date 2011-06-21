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
import os.path

try:
    from collections import OrderedDict as dict
except ImportError:
    pass


FILEINFOS = dict()
PACKAGE_MAKERS = dict()
COLLECTORS = dict()

TEMPLATE_SEARCH_PATHS = ["/usr/share/pmaker/templates", ]

COMPRESSORS = (
    # cmd, extension, am_option,
    ("xz",    "xz",  "no-dist-gzip dist-xz"),
    ("bzip2", "bz2", "no-dist-gzip dist-bzip2"),
    ("gzip",  "gz",  ""),
)


CONFLICTS_STATEDIR = "/var/lib/%(name)s-overrides"
CONFLICTS_SAVEDIR = os.path.join(CONFLICTS_STATEDIR, "saved")
CONFLICTS_NEWDIR = os.path.join(CONFLICTS_STATEDIR, "new")


TYPE_FILE    = "file"
TYPE_DIR     = "dir"
TYPE_SYMLINK = "symlink"
TYPE_OTHER   = "other"
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
        "arrange build aux files such like configure.ac, Makefile.am, rpm spec" + \
        "file, debian/* and so on. python-cheetah will be needed."),

    (STEP_CONFIGURE, "Configuring src distribution: %(pname)s",
        "setup src dir to run './configure'. autotools will be needed"),

    (STEP_SBUILD, "Building src package: %(pname)s", "build src package[s]"),

    (STEP_BUILD, "Building bin packages: %(pname)s", "build binary package[s]"),
)


CHEETAH_ENABLED = False
JSON_ENABLED = False
PYXATTR_ENABLED = False


try:
    from Cheetah.Template import Template
    CHEETAH_ENABLED = True
    UPTO = STEP_BUILD

except ImportError:
    UPTO = STEP_SETUP
    logging.warn("python-cheetah is not found. It will go up to \"%s\" step." % STEP_SETUP)


try:
    import json
    JSON_ENABLED = True

except ImportError:
    try:
        import simplejson as json
        JSON_ENABLED = True

    except ImportError:
        logging.warn("json module is not found. JSON support will be disabled.")


try:
    import xattr  # pyxattr
    PYXATTR_ENABLED = True

except ImportError:
    logging.warn("pyxattr module is not found. Its support will be disabled.")


# vim: set sw=4 ts=4 expandtab:
