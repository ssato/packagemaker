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

import BeautifulSoup
import logging
import os.path
import re
import sys


def get_download_url(name, base_url="pypi.python.org/pypi/"):
    """
    """
    pi_url = base_url + name
    page = U.urlread(pi_url)

    if page is None:
        logging.warn("Could not get the www page content: " + name)

    soup = BeautifulSoup.BeautifulSoup(page)

    reg = re.compile(r"(http://pypi.python.org/packages/source/.*)#md5=.*")
    t = soup.find("a", attrs={"href": reg})
    if t is None:
        logging.warn("Could not resolve download url: " + name)
        return None

    download = reg.match(dict(t.attrs)["href"]).groups()[0]
    return download


def parse_pypi_page(name, base_url="pypi.python.org/pypi/"):
    """
    """
    pi_url = base_url + name
    page = U.urlread(pi_url)

    if page is None:
        logging.warn("Could not get the www page content: " + name)

    soup = BeautifulSoup.BeautifulSoup(page)

    summary = soup.find("meta", attrs={"name": "description"})
    if summary is not None:
        summary = dict(summary).attrs).get("content", "")

    url = None
    t = soup.find("strong", text=re.compile(r"^home.*page.*", re.IGNORECASE))
    if t is not None:
        href = t.parent.parent.find("a").attrs).get("href")
        if href is not None:
            url = dict(href.attrs).get("href", None)

    download = None
    reg = re.compile(r"(http://pypi.python.org/packages/source/.*)#md5=.*")
    t = soup.find("a", attrs={"href": reg})
    if t is not None:
        download = reg.match(dict(t.attrs)["href"]).groups()[0]

    return Bunch(
        name=name,
        url=url,
        download=download,
    )


# vim:sw=4 ts=4 et:
