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
from pmaker.models.Bunch import Bunch

import glob
import itertools
import logging
import re


INT_PATTERN = re.compile(r"^(\d|([1-9]\d+))$")
BOOL_PATTERN = re.compile(r"^(true|false)$", re.I)
STR_PATTERN = re.compile(r"^['\"](.*)['\"]$")


def parse_single(s):
    """
    Very simple parser to parse expressions represent some single values.

    >>> assert 0 == parse_single("0")
    >>> assert 123 == parse_single("123")
    >>> assert True == parse_single("True")
    >>> assert "a string" == parse_single("a string")
    >>> assert "0.1" == parse_single("0.1")
    >>> parse_single("    a string contains extra whitespaces     ")
    'a string contains extra whitespaces'
    """
    def matched(pat, s):
        return pat.match(s) is not None

    s = s.strip()

    if not s:
        return ""

    if matched(BOOL_PATTERN, s):
        return bool(s)

    if matched(INT_PATTERN, s):
        return int(s)

    if matched(STR_PATTERN, s):
        return s[1:-1]

    return s


def parse_list(s, sep=","):
    """
    Simple parser to parse expressions reprensent some list values.

    :param sep: Char to separate items of list.

    >>> assert parse_list("") == []
    >>> assert parse_list("a,b") == ["a", "b"]
    >>> assert parse_list("1,2") == [1, 2]
    >>> assert parse_list("a,b,") == ["a", "b"]
    """
    return [parse_single(x) for x in s.split(sep) if x]


def parse_attrlist(s, avs_sep=":", vs_sep=",", as_sep=";"):
    """
    Simple parser to parse expressions in the form of
    [ATTR1:VAL0,VAL1,...;ATTR2:VAL0,VAL2,..].

    :param s: input string
    :param avs_sep:  char to separate attribute and values
    :param vs_sep:  char to separate values
    :param as_sep:  char to separate attributes

    >>> parse_attrlist("requires:bash,zsh")
    [('requires', ['bash', 'zsh'])]
    >>> parse_attrlist("obsoletes:sysdata;conflicts:sysdata-old")
    [('obsoletes', ['sysdata']), ('conflicts', ['sysdata-old'])]
    """
    def attr_and_values(s):
        for rel in parse_list(s, as_sep):
            if avs_sep not in rel or rel.endswith(avs_sep):
                continue

            (_attr, _values) = parse_list(rel, avs_sep)
            _values = parse_list(_values, vs_sep)

            if _values:
                yield (_attr, _values)

    return [(a, vs) for a, vs in attr_and_values(s)]


def parse(s):
    if ":" in s:
        return parse_attrlist(s)
    elif "," in s:
        return parse_list(s)
    else:
        return parse_single(s)


def parse_line_of_filelist(line):
    """
    Parse a line of filelist (plain) and returns an object holding metadata of
    files.

    >>> line = "/etc/resolv.conf"
    >>> parse_line_of_filelist(line + "\\n")
    (['/etc/resolv.conf'], {})
    >>> line += ",install_path=/var/lib/network/resolv.conf,uid=0,gid=0"
    >>> (paths, attrs) = parse_line_of_filelist(line)
    >>> assert paths[0] == "/etc/resolv.conf"
    >>> assert attrs.install_path == "/var/lib/network/resolv.conf"
    >>> assert attrs.uid == 0
    >>> assert attrs.gid == 0
    """
    ss = parse_list(line.rstrip().strip(), ",")
    pp = ss[0]

    paths = "*" in pp and glob.glob(pp) or [pp]

    avs = [
        av for av in (parse_list(a, "=") for a in ss[1:]) if av
    ]
    attrs = Bunch((a, parse_single(str(v))) for a, v in avs)
    if "*" in pp:
        attrs.create = False

    return (paths, attrs)


# vim:sw=4 ts=4 et:
