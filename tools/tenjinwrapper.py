#! /usr/bin/python
#
# Copyright (C) 2011 Satoru SATOH <ssato@redhat.com>
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
import pmaker.tenjinwrapper as TW
import optparse
import sys


def main():
    defaults = dict(
        context={},
    )

    p = optparse.OptionParser("Usage: %prog [Options] TEMPLATE_PATH")
    p.set_defaults(**defaults)

    p.add_option("-C", "--context", help="Specify str represents context data")

    (opts, args) = p.parse_args()

    if not args:
        p.print_usage()
        sys.exit(-1)

    template_path = args[0]

    if opts.context:
        opts.context = eval(opts.context)

    content = TW.template_compile(template_path, opts.context)
    print content


if __name__ == '__main__':
    main()


# vim:sw=4 ts=4 et:
