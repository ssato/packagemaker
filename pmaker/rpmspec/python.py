#
# Copyright (C) 2011 Satoru SATOH <ssato @ redhat.com>
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
import pmaker.utils as U

import logging
import os.path
import re
import sys


def get_download_url(name, base_url="pypi.python.org/pypi/"):
    """

    pi_url example: http://pypi.python.org/pypi/pyev/

    search pattern: 
        '<a href="<URL>#md5=..."><NAME>-<VERSION>.tar.gz</a>

        where <X> = Initial character of name
              <NAME> = name
              <VERSION> = version
              <DBASE_URL> = "http://pypi.python.org/packages/source"
              <URL> = <DBASE_URL>/<X>/<NAME>/<NAME>-<VERSION>.tar.gz

    """
    pi_url = base_url + name
    page = U.urlread(pi_url)

    if page is None:
        logging.warn("Could not get the www page content: " + name)
        return None

    reg = re.compile(
        r".*(http://pypi.python.org/packages/source/[^#]+)#md5=.*"
    )

    ls = [l for l in page.split("\n") if reg.match(l)]
    if not ls:
        logging.warn("Could not get the download url: " + name)
        return None

    m = reg.match(ls[0])
    assert m is not None, str(ls)

    download = m.groups()[0]
    return download


# vim:sw=4 ts=4 et:
