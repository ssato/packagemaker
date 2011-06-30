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
from distutils.sysconfig import get_python_lib

from pmaker.globals import *
from pmaker.rpmutils import *
from pmaker.config import Config, option_parser
from pmaker.package import Package
from pmaker.utils import do_nothing

import glob
import inspect
import logging
import optparse
import os
import os.path
import sys


PYTHON_LIBDIR = get_python_lib()



def load_plugins(libdir=PYTHON_LIBDIR):
    plugins = glob.glob(os.path.join(libdir, "pmaker", "plugins", "*.py"))

    for modpy in plugins:
        modn = os.path.basename(modpy).replace(".py")

        if modn == "__init__":
            continue

        mod = __import__("pmaker.plugins.%s" % modn)
        init_f = getattr(mod, "init", do_nothing)
        init_f()
            


def main(argv=sys.argv, compressors=COMPRESSORS, templates=TEMPLATES):
    global TEMPLATES, PYXATTR_ENABLED

    loglevel = logging.INFO
    logdatefmt = "%H:%M:%S" # too much? "%a, %d %b %Y %H:%M:%S"
    logformat = "%(asctime)s [%(levelname)-4s] %(message)s"

    logging.basicConfig(level=loglevel, format=logformat, datefmt=logdatefmt)

    p = config.option_parser()
    (options, args) = p.parse_args(argv[1:])

    loglevel = options.verbose and logging.INFO or logging.WARN
    if options.debug:
        loglevel = logging.DEBUG

    logging.getLogger().setLevel(loglevel)

    if len(args) < 1:
        p.print_usage()
        sys.exit(1)

    filelist = args[0]

    if not options.name:
        sys.stderr.write("You must specify the package name with \"--name\" option\n")
        options.name = raw_input("You must specify the package name. Name: ")

    if options.scriptlets:
        try:
            scriptlets = open(options.scriptlets).read()
        except IOError:
            logging.warn(" Could not open %s to read scriptlets" % options.scriptlets)
            scriptlets = ""

        options.scriptlets = scriptlets

    pkg = Package(options)

    do_packaging(pkg, filelist, options)


if __name__ == '__main__':
    main()

# vim: set sw=4 ts=4 expandtab:
