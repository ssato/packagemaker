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
import pmaker.options as O
import pmaker.pkgdata as P
import pmaker.collectors.FilelistCollectors as Collectors
import pmaker.backend.registry as Backends

import logging
import sys


def main(argv=sys.argv):
    logging.basicConfig(format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")  # or "%Y-%m-%d %H:%M:%S",

    o = O.Options()
    (opts, args) = o.parse_args(argv[1:])

    listfile = args[0] if args else opts.config

    ccls = Collectors.map().get(opts.input_type)
    collector = ccls(listfile, opts)

    fs = collector.collect()

    if not fs:
        raise RuntimeError("Failed to collect files from " + listfile)

    pkgdata = P.PkgData(opts, fs)

    bcls = Backends.map().get(opts.driver)
    backend = bcls(pkgdata)
    rc = backend.run()

    return rc


if __name__ == '__main__':
    sys.exit(main())


# vim:sw=4:ts=4:et:
