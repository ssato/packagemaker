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
from pmaker.globals import *
from pmaker.config import parse_args
from pmaker.package import Package
from pmaker.utils import do_nothing
from pmaker.collectors.Collectors import FilelistCollector
from pmaker.makers.PackageMaker import AutotoolsTgzPackageMaker

import distutils.sysconfig
import glob
import inspect
import logging
import optparse
import os
import os.path
import pprint
import sys


PYTHON_LIBDIR = distutils.sysconfig.get_python_lib()

LOG_LEVELS = [logging.WARN, logging.INFO, logging.DEBUG]


def load_plugins(libdir=PYTHON_LIBDIR):
    plugins = glob.glob(os.path.join(libdir, "pmaker", "plugins", "*.py"))

    for modpy in plugins:
        modn = os.path.basename(modpy).replace(".py")

        if modn == "__init__":
            continue

        mod = __import__("pmaker.plugins.%s" % modn)
        init_f = getattr(mod, "init", do_nothing)
        init_f()


def _get_class(ctype, cpool, default):
    """
    Get class from classes pool by its type. If no class found for given type,
    it will return the given default.

    @param  ctype    'Type' of class to find. 'Type' varies dependent on class
    @param  cpool    Class pool
    @param  default  Default class returned if no class found for the type
    """
    cls = cpool.get(ctype, default)
    logging.info("Use %s (type=%s)" % (cls.__name__, ctype))

    return cls


def init_log():
    datefmt = "%H:%M:%S" # too much? "%a, %d %b %Y %H:%M:%S"
    fmt = "%(asctime)s [%(levelname)-4s] %(message)s"

    logging.basicConfig(level=logging.INFO, format=fmt, datefmt=datefmt)


def main(argv=sys.argv, collector=COLLECTORS):
    init_log()

    (parser, options, args) = parse_args(argv[1:], upto=UPTO,
            build_steps=BUILD_STEPS, drivers=PACKAGE_MAKERS,
            itypes=COLLECTORS, tmpl_search_paths=TEMPLATE_SEARCH_PATHS)

    loglevel = LOG_LEVELS[options.verbosity]
    logging.getLogger().setLevel(loglevel)

    if len(args) < 1:
        parser.print_usage()
        sys.exit(1)

    listfile = args[0]

    if not options.name:
        sys.stderr.write("You must specify the package name with \"--name\" option\n")
        options.name = raw_input("You must specify the package name. Name: ")

    if options.format:
        options.driver = options.driver.split(".")[0] + "." + options.format

    if options.scriptlets:
        try:
            scriptlets = open(options.scriptlets).read()
        except IOError:
            logging.warn(" Could not open %s to read scriptlets" % options.scriptlets)
            scriptlets = ""

        options.scriptlets = scriptlets

    pkg = Package(options)
    #pprint.pprint(pkg.as_dict())

    ccls = _get_class(options.itype, COLLECTORS, FilelistCollector)
    collector = ccls(listfile, options)
    fis = collector.collect()

    #logging.debug("Collected fileinfos: " + ", ".join(fi.path for fi in fis))

    dcls = _get_class(options.driver, PACKAGE_MAKERS, AutotoolsTgzPackageMaker)
    driver = dcls(pkg, fis, options)
    driver.run()


if __name__ == '__main__':
    main()

# vim: set sw=4 ts=4 expandtab:
