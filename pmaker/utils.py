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

import copy
import datetime
import logging
import operator


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
    from Cheetah.Template import Template
    CHEETAH_ENABLED = True

except ImportError:
    logging.warn("python-cheetah is not found.")
    UPTO = STEP_SETUP

    def Template(*args, **kwargs):
        raise RuntimeError("python-cheetah is missing and cannot proceed any more.")


try:
    from hashlib import sha1 # md5, sha256, sha512

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


# globals:
(DATE_FMT_RFC2822, DATE_FMT_SIMPLE) = (0, 1)



def dicts_comp(lhs, rhs, keys=False):
    """Compare dicts. $rhs may have keys (and values) $lhs does not have.

    >>> dicts_comp({},{})
    True
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
    >>> d2 = copy.copy(d0)
    >>> d2["c"] = 3
    >>> dicts_comp(d0, d2)
    False
    >>> dicts_comp(d0, d2, ("a", "b"))
    True
    """
    if lhs == {}:
        return True
    elif rhs == {}:
        return False
    else:
        return all((lhs.get(key) == rhs.get(key)) for key in keys and keys or lhs.keys())


def memoize(fn):
    """memoization decorator.
    """
    cache = {}

    def wrapped(*args, **kwargs):
        key = repr(args) + repr(kwargs)
        if not cache.has_key(key):
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

    TODO: What should be done when any exceptions such like IOError (e.g. could
    not open $filepath) occur?
    """
    if not filepath:
        return "0" * len(algo("").hexdigest())

    f = open(filepath, "r")
    m = algo()

    while True:
        data = f.read(buffsize)
        if not data:
            break
        m.update(data)

    f.close()

    return m.hexdigest()


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


def date(type=None):
    """TODO: how to output in rfc2822 format w/o email.Utils.formatdate?
    ("%z" for strftime does not look working.)
    """
    if type == DATE_FMT_RFC2822:
        fmt = "%a, %d %b %Y %T +0000"
    elif type == DATE_FMT_SIMPLE:
        fmt = "%Y%m%d"
    else:
        fmt = "%a %b %_d %Y"

    return datetime.datetime.now().strftime(fmt)


def do_nothing(*args, **kwargs):
    return


def on_debug_mode():
    return logging.getLogger().level < logging.INFO


def compile_template(template, params, is_file=False):
    """
    TODO: Add test case that $template is a filename.

    >>> tmpl_s = "a=$a b=$b"
    >>> params = {"a": 1, "b": "b"}
    >>> 
    >>> assert "a=1 b=b" == compile_template(tmpl_s, params)
    """
    if is_file:
        tmpl = Template(file=template, searchList=params)
    else:
        tmpl = Template(source=template, searchList=params)

    return tmpl.respond()


def createdir(targetdir, mode=0700):
    """Create a dir with specified mode.
    """
    logging.debug(" Creating a directory: %s" % targetdir)

    if os.path.exists(targetdir):
        if os.path.isdir(targetdir):
            logging.warn(" Directory already exists! Skip it: %s" % targetdir)
        else:
            raise RuntimeError(" Already exists but not a directory: %s" % targetdir)
    else:
        os.makedirs(targetdir, mode)


def rm_rf(target):
    """ "rm -rf" in python.

    >>> d = tempfile.mkdtemp(dir="/tmp")
    >>> rm_rf(d)
    >>> rm_rf(d)
    >>> 
    >>> d = tempfile.mkdtemp(dir="/tmp")
    >>> for c in "abc":
    ...     os.makedirs(os.path.join(d, c))
    >>> os.makedirs(os.path.join(d, "c", "d"))
    >>> open(os.path.join(d, "x"), "w").write("test")
    >>> open(os.path.join(d, "a", "y"), "w").write("test")
    >>> open(os.path.join(d, "c", "d", "z"), "w").write("test")
    >>> 
    >>> rm_rf(d)
    """
    if not os.path.exists(target):
        return

    if os.path.isfile(target) or os.path.islink(target):
        os.remove(target)
        return 

    warnmsg = "You're trying to rm -rf / !"
    assert target != "/", warnmsg
    assert os.path.realpath(target) != "/", warnmsg

    xs = glob.glob(os.path.join(target, "*")) + glob.glob(os.path.join(target, ".*"))

    for x in xs:
        if os.path.isdir(x):
            rm_rf(x)
        else:
            os.remove(x)

    if os.path.exists(target):
        os.removedirs(target)


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


def distdata_in_makefile_am(paths, srcdir="src"):
    """
    @paths  file path list

    >>> ps0 = ["/etc/resolv.conf", "/etc/sysconfig/iptables"]
    >>> rs0 = [{"dir": "/etc", "files": ["src/etc/resolv.conf"], "id": "0"}, {"dir": "/etc/sysconfig", "files": ["src/etc/sysconfig/iptables"], "id": "1"}]
    >>> 
    >>> ps1 = ps0 + ["/etc/sysconfig/ip6tables", "/etc/modprobe.d/dist.conf"]
    >>> rs1 = [{"dir": "/etc", "files": ["src/etc/resolv.conf"], "id": "0"}, {"dir": "/etc/sysconfig", "files": ["src/etc/sysconfig/iptables", "src/etc/sysconfig/ip6tables"], "id": "1"}, {"dir": "/etc/modprobe.d", "files": ["src/etc/modprobe.d/dist.conf"], "id": "2"}]
    >>> 
    >>> _cmp = lambda ds1, ds2: all([utils.dicts_comp(*dt) for dt in zip(ds1, ds2)])
    >>> 
    >>> rrs0 = distdata_in_makefile_am(ps0)
    >>> rrs1 = distdata_in_makefile_am(ps1)
    >>> 
    >>> assert _cmp(rrs0, rs0), "expected %s but got %s" % (str(rs0), str(rrs0))
    >>> assert _cmp(rrs1, rs1), "expected %s but got %s" % (str(rs1), str(rrs1))
    """
    cntr = count()

    return [
        {
            "id": str(cntr.next()),
            "dir":d,
            "files": [os.path.join("src", p.strip(os.path.sep)) for p in ps]
        } \
        for d,ps in groupby(paths, os.path.dirname)
    ]


# vim: set sw=4 ts=4 expandtab:
