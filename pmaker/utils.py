#
# Copyright (C) 2011 - 2013 Satoru SATOH <satoru.satoh @ gmail.com>
# Copyright (C) 2013 Red Hat, Inc.
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
import pmaker.globals as G
import pmaker.models.Bunch as B

import copy
import datetime
import glob
import itertools
import locale
import logging
import operator
import os
import re
import stat
import urllib2


try:
    from functools import partial as curry, reduce as foldl
except ImportError:
    foldl = reduce

    def curry(func, *args, **keywords):
        """@see 'functools.partial' section in Python Library Reference
        """
        def newfunc(*fargs, **fkeywords):
            newkeywords = keywords.copy()
            newkeywords.update(fkeywords)
            return func(*(args + fargs), **newkeywords)

        newfunc.func = func
        newfunc.args = args
        newfunc.keywords = keywords

        return newfunc


try:
    from hashlib import sha1  # md5, sha256, sha512

except ImportError:  # python < 2.5
    from sha import sha as sha1


try:
    all

except NameError:  # python < 2.5
    def all(xs):
        for x in xs:
            if not x:
                return False
        return True


try:
    any

except NameError:
    def any(xs):
        for x in xs:
            if x:
                return True
        return False


def dicts_comp(lhs, rhs, keys=None, strict=False):
    """Compare dicts. $rhs may have keys (and values) $lhs does not have.

    :param lhs:  target dict
    :param rhs:  a dict to compare with
    :param keys: keys to compare
    :param strict: Compare if lhs and rhs have same keys and values exactly
                   when True.

    >>> dicts_comp({},{})
    True
    >>> dicts_comp({}, {"a":1})
    False
    >>> dicts_comp({"a":1},{})
    False
    >>> d0 = {"a": 0, "b": 1, "c": 2}
    >>> d1 = copy.copy(d0)
    >>> dicts_comp(d0, d1)
    True
    >>> d1["d"] = 3
    >>> dicts_comp(d0, d1)
    True
    >>> dicts_comp(d0, d1, ("d"))
    False
    >>> dicts_comp(d0, d1, strict=True)
    False
    >>> d2 = copy.copy(d0)
    >>> d2["c"] = 3
    >>> dicts_comp(d0, d2)
    False
    >>> dicts_comp(d0, d2, ("a", "b"))
    True
    """
    if lhs and rhs:
        if not keys:
            if strict:
                keys = set(lhs.keys() + rhs.keys())
            else:
                keys = lhs.keys()

        return all(lhs.get(k) == rhs.get(k) for k in keys)
    else:
        return lhs == rhs


def memoize(fn):
    """memoization decorator.
    """
    cache = {}

    def wrapped(*args, **kwargs):
        key = repr(args) + repr(kwargs)
        if key not in cache:
            cache[key] = fn(*args, **kwargs)

        return cache[key]

    return wrapped


class memoized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.

    Originally came from
    http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        try:
            return self.cache[args]

        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value

        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)

    def __repr__(self):
        """Return the function's docstring.
        """
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """Support instance methods.
        """
        return curry(self.__call__, obj)


@memoize
def checksum(filepath="", algo=sha1, buffsize=8192):
    """compute and check md5 or sha1 message digest of given file path.

    TODO: What should be done when any exceptions such like IOError (e.g.
    could not open $filepath) occur?
    """
    if not filepath:
        return "0" * len(algo("").hexdigest())

    try:
        f = open(filepath, "r")
    except IOError:
        return "0" * len(algo("").hexdigest())

    m = algo()

    while True:
        data = f.read(buffsize)
        if not data:
            break
        m.update(data)

    f.close()

    return m.hexdigest()


def st_mode_to_mode(st_mode):
    """Convert st_mode (os.lstat().st_mode) to mode string, e.g. "0644"
    """
    m = stat.S_IMODE(st_mode & 0777)
    return m == 0 and "0000" or oct(m)


def is_foldable(xs):
    """@see http://www.haskell.org/haskellwiki/Foldable_and_Traversable

    >>> is_foldable([])
    True
    >>> is_foldable(())
    True
    >>> is_foldable(x for x in range(3))
    True
    >>> is_foldable(None)
    False
    >>> is_foldable(True)
    False
    >>> is_foldable(1)
    False
    """
    return isinstance(xs, (list, tuple)) or callable(getattr(xs, "next", None))


def listplus(list_lhs, foldable_rhs):
    """
    (++) in python.
    """
    return list_lhs + list(foldable_rhs)


@memoize
def flatten(xss):
    """
    >>> flatten([])
    []
    >>> flatten([[1,2,3],[4,5]])
    [1, 2, 3, 4, 5]
    >>> flatten([[1,2,[3]],[4,[5,6]]])
    [1, 2, 3, 4, 5, 6]

    tuple:

    >>> flatten([(1,2,3),(4,5)])
    [1, 2, 3, 4, 5]

    generator expression:

    >>> flatten((i, i * 2) for i in range(0,5))
    [0, 0, 1, 2, 2, 4, 3, 6, 4, 8]
    """
    if is_foldable(xss):
        return foldl(operator.add, (flatten(xs) for xs in xss), [])
    else:
        return [xss]


def concat(xss):
    """
    >>> concat([[]])
    []
    >>> concat((()))
    []
    >>> concat([[1,2,3],[4,5]])
    [1, 2, 3, 4, 5]
    >>> concat([[1,2,3],[4,5,[6,7]]])
    [1, 2, 3, 4, 5, [6, 7]]
    >>> concat(((1,2,3),(4,5,[6,7])))
    [1, 2, 3, 4, 5, [6, 7]]
    >>> concat(((1,2,3),(4,5,[6,7])))
    [1, 2, 3, 4, 5, [6, 7]]
    >>> concat((i, i*2) for i in range(3))
    [0, 0, 1, 2, 2, 4]
    """
    assert is_foldable(xss)

    return foldl(listplus, (xs for xs in xss), [])


@memoize
def unique(xs, cmp=cmp, key=None):
    """Returns new sorted list of no duplicated items.

    >>> unique([])
    []
    >>> unique([0, 3, 1, 2, 1, 0, 4, 5])
    [0, 1, 2, 3, 4, 5]
    """
    if xs == []:
        return xs

    ys = sorted(xs, cmp=cmp, key=key)

    if ys == []:
        return ys

    ret = [ys[0]]

    for y in ys[1:]:
        if y == ret[-1]:
            continue
        ret.append(y)

    return ret


def true(x):
    return True


def singleton(cls):
    instances = dict()

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()

        return instances[cls]

    return getinstance


@memoize
def is_superuser():
    return os.getuid() == 0


def do_nothing(*args, **kwargs):
    return


def on_debug_mode():
    return logging.getLogger().level < logging.INFO


def createdir(targetdir, mode=0700):
    """Create a dir with specified mode.
    """
    logging.debug("Creating a directory: " + targetdir)

    if os.path.exists(targetdir):
        if os.path.isdir(targetdir):
            logging.warn("Directory already exists! Skip it: " + targetdir)
        else:
            raise RuntimeError(
                " Already exists but not a directory: " + targetdir
            )
    else:
        os.makedirs(targetdir, mode)


def rm_rf(target):
    """ 'rm -rf' in python.
    """
    if not os.path.exists(target):
        return

    if os.path.isfile(target) or os.path.islink(target):
        os.remove(target)
        return

    warnmsg = "You're trying to rm -rf / !"
    assert target != "/", warnmsg
    assert os.path.realpath(target) != "/", warnmsg

    xs = glob.glob(os.path.join(target, "*")) + \
         glob.glob(os.path.join(target, ".*"))

    for x in xs:
        if os.path.isdir(x):
            rm_rf(x)
        else:
            os.remove(x)

    if os.path.exists(target):
        os.removedirs(target)


def format_date(type=None):
    """
    TODO: how to output in rfc2822 format w/o email.Utils.formatdate?
    ("%z" for strftime does not look working.)
    """
    locale.setlocale(locale.LC_TIME, "C")

    if type == G.DATE_FMT_RFC2822:
        fmt = "%a, %d %b %Y %T +0000"
    elif type == G.DATE_FMT_SIMPLE:
        fmt = "%Y%m%d"
    else:
        fmt = "%a %b %_d %Y"

    return datetime.datetime.now().strftime(fmt)


def cache_needs_updates_p(cache_file, expires=0):
    if expires == 0 or not os.path.exists(cache_file):
        return True

    try:
        mtime = os.stat(cache_file).st_mtime
    except OSError:  # It indicates that the cache file cannot be updated.
        return True  # FIXME: How to handle the above case?

    cur_time = datetime.datetime.now()
    cache_mtime = datetime.datetime.fromtimestamp(mtime)

    delta = cur_time - cache_mtime  # TODO: How to do if it's negative value?

    return (delta >= datetime.timedelta(expires))


def sort_out_paths_by_dir(paths):
    """
    Sort out files by dirs.

    :param paths: path list, e.g.
        ["/etc/resolv.conf", "/etc/sysconfig/iptables",
            "/etc/sysconfig/network"]

    :return: path list grouped by dirs, e.g.
        [{"dir": "/etc", "files": ["/etc/resolv.conf"], "id": "0"},
         {"dir": "/etc/sysconfig", "files": ["/etc/sysconfig/iptables"],
            "id": "1"}]
    """
    cntr = itertools.count()

    return [B.Bunch(id=str(cntr.next()), dir=d, files=list(ps)) \
            for d, ps in itertools.groupby(paths, os.path.dirname)]


def parse_conf_value(s):
    """Simple and naive parser to parse value expressions in config files.

    >>> assert 0 == parse_conf_value("0")
    >>> assert 123 == parse_conf_value("123")
    >>> assert True == parse_conf_value("True")
    >>> assert [1,2,3] == parse_conf_value("[1,2,3]")
    >>> assert "a string" == parse_conf_value("a string")
    >>> assert "0.1" == parse_conf_value("0.1")
    """
    intp = re.compile(r"^([0-9]|([1-9][0-9]+))$")
    boolp = re.compile(r"^(true|false)$", re.I)
    listp = re.compile(r"^(\[\s*((\S+),?)*\s*\])$")
    strp = re.compile(r"^['\"](.*)['\"]$")

    def matched(pat, s):
        m = pat.match(s)
        return m is not None

    if not s:
        return ""

    if matched(boolp, s):
        return bool(s)

    if matched(intp, s):
        return int(s)

    if matched(strp, s):
        return s[1:-1]

    if matched(listp, s):
        return eval(s)  # TODO: too danger. safer parsing should be needed.

    return s


def parse_list_str(optstr, sep=","):
    """
    Simple parser for optstr gives a list of items separated with "," (comma).

    >>> assert parse_list_str("") == []
    >>> assert parse_list_str("a,b") == ["a", "b"]
    >>> assert parse_list_str("a,b,") == ["a", "b"]
    """
    return [p for p in optstr.split(sep) if p]


def conflicts_dirs(pname):
    """
    Dirs to save or put files owned by this and other packages sametime.

    :param name: The name of the package to be built.
    """
    p = dict(name=pname)

    return (G.CONFLICTS_SAVEDIR % p, G.CONFLICTS_NEWDIR % p)


def urlread(url, data=None, headers={}):
    """
    Open given url and returns its contents or None.
    """
    req = urllib2.Request(url=url, data=data, headers=headers)

    try:
        return urllib2.urlopen(req).read()
    except:
        return None


# vim:sw=4:ts=4:et:
