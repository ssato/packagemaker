
# Copyright (C) 2011 Satoru SATOH <satoru.satoh @ gmail.com>
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
import pmaker.globals as G
import pmaker.utils as U

import bunch as B
import cPickle as pickle
import datetime
import grp
import locale
import logging
import os
import os.path
import pwd
import rpm
import subprocess


try:
    from collections import OrderedDict as dict
except ImportError:
    pass


RPM_FILELIST_CACHE = os.path.join(
    os.environ.get("HOME", "."), ".cache", "pmaker.rpm.filelist.pkl"
)

# RpmFi (FileInfo) keys:
RPM_FI_KEYS = (
    "path",
    "size",
    "mode",
    "mtime",
    "flags",
    "rdev",
    "inode",
    "nlink",
    "state",
    "vflags",
    "uid",
    "gid",
    "checksum",
)

# FIXME: Fix naming convention of relation keys.
RPM_RELATIONS = {
    "buildrequires": "BuildRequires",
    "requires": "Requires",
    "requires.pre": "Requires(pre)",
    "requires.preun": "Requires(preun)",
    "requires.post": "Requires(post)",
    "requires.postun": "Requires(postun)",
    "requires.verify": "Requires(verify)",
    "conflicts": "Conflicts",
    "provides": "Provides",
    "obsoletes": "Obsoletes",
}


@U.memoize
def is_rpmdb_available():
    try:
        rc = subprocess.check_call(
            "rpm -qf /bin/sh 2>&1 > /dev/null", shell=True
        )
        return bool(rc == 0)

    except subprocess.CalledProcessError, e:
        return False


def changelog_date(dt=None):
    """
    Returns a string represents built (packaging) date in %changelog section in
    the rpm spec.

    :param dt: datetime object or None.

    >>> dt = datetime.datetime(2012, 1, 3)  # 2010.01.03
    >>> changelog_date(dt)
    'Tue Jan  3 2012'
    """
    locale.setlocale(locale.LC_TIME, "C")
    return (
        datetime.datetime.now() if dt is None else dt
    ).strftime("%a %b %e %Y")


def rpmh2nvrae(h):
    """Transform rpm header (like) object to a dict.

    @h  Rpm header-like object to allow access such like $h["name"].
    """
    d = dict(
        (k, h[k]) for k in ("name", "version", "release", "arch", "epoch")
    )
    d["epoch"] = str(normalize_epoch(d["epoch"]))

    return B.Bunch(**d)


def ts(rpmdb_path=None):
    if rpmdb_path is not None:
        rpm.addMacro("_dbpath", rpmdb_path)

    return rpm.TransactionSet()


def normalize_epoch(epoch):
    """

    >>> normalize_epoch("(none)")  # rpmdb style
    0
    >>> normalize_epoch(" ")  # yum style
    0
    >>> normalize_epoch("0")
    0
    >>> normalize_epoch("1")
    1
    """
    if epoch is None:
        return 0
    else:
        if isinstance(epoch, str):
            epoch = epoch.strip()
            if epoch and epoch != "(none)":
                return int(epoch)
            else:
                return 0
        else:
            return epoch  # int?


def srcrpm_name_by_rpmspec(rpmspec):
    """Returns the name of src.rpm gotten from given RPM spec file.
    """
    cmd = "rpm -q --specfile --qf \"%{n}-%{v}-%{r}.src.rpm\n\" " + rpmspec
    out = subprocess.check_output(cmd, shell=True)
    return out.split("\n")[0]


def srcrpm_name_by_rpmspec_2(rpmspec, rpmdb_path=None):
    """Returns the name of src.rpm gotten from given RPM spec file.

    Utilize rpm python binding instead of calling "rpm" command like above.

    FIXME: rpm-python does not look stable and dumps core often.
    """
    spec = ts(rpmdb_path).parseSpec(rpmspec).packages[0]
    h = spec.packages[0].header
    return "%s-%s-%s.src.rpm" % (h["n"], h["v"], h["r"])


def info_by_path(path, fi_keys=RPM_FI_KEYS, rpmdb_path=None):
    """Get meta data of file or dir from RPM Database.

    @path    Path of the file or directory (relative or absolute)
    @return  A dict; keys are fi_keys
    """
    apath = os.path.abspath(path)

    try:
        fis = [
            h.fiFromHeader() for h in \
                ts(rpmdb_path).dbMatch("basenames", apath)
        ]
        if fis:
            xs = [x for x in fis[0] if x and x[0] == apath]
            if xs:
                return dict(zip(fi_keys, xs[0]))
    except:  # FIXME: Careful excpetion handling
        pass

    return dict()


@U.memoize
def filelist(cache=True, expires=1, pkl_proto=pickle.HIGHEST_PROTOCOL,
        rpmdb_path=None, cache_file=RPM_FILELIST_CACHE):
    """
    TODO: It should be a heavy and time-consuming task. How to shorten this
    time? - caching, utilize yum's file list database or whatever.
    """
    data = None
    cachedir = os.path.dirname(cache_file)

    if not os.path.exists(cachedir):
        os.makedirs(cachedir, 0755)

    if cache and not U.cache_needs_updates_p(cache_file, expires):
        try:
            data = pickle.load(open(cache_file, "rb"))
            logging.debug("Could load the cache: %s" % cache_file)
        except:
            logging.warn("Could not load the cache: %s" % cache_file)
            date = None

    if data is None:
        data = dict(
            concat(((f, rpmh2nvrae(h)) for f in h["filenames"]) \
                for h in ts(rpmdb_path).dbMatch())
        )

        try:
            # TODO: How to detect errors during/after pickle.dump.
            pickle.dump(data, open(cache_file, "wb"), pkl_proto)
            logging.debug("Could save the cache: %s" % cache_file)
        except:
            logging.warn("Could not save the cache: %s" % cache_file)

    return data


try:
    from yum import rpmsack
    rpmdb = rpmsack.RPMDBPackageSack()

    @U.memoize
    def rpm_search_provides_by_path(path):
        rs = rpmdb.searchProvides(path)
        return rpmh2nvrae(rs[0]) if rs else B.Bunch()

except ImportError:
    @U.memoize
    def rpm_search_provides_by_path(path, rpmdb_path=None):
        database = filelist(rpmdb_path=rpmdb_path)
        return B.Bunch(**database.get(path, dict()))


def __rpm_attr(fo):
    """
    Returns "%attr(...)" to specify the file/dir attribute for given fo object,
    which will be used in the %files section in rpm spec.

    >>> from pmaker.models.FileObjects import FileObject
    >>> fi = FileObject(path="/dummy/path", mode="0664")
    >>> assert __rpm_attr(fi) == "%attr(0664, -, -)"
    >>> fi = FileObject(path="/bin/foo", mode="0755", uid=1, gid=1)
    >>> assert __rpm_attr(fi) == "%attr(0755, bin, bin)"
    >>> fi = FileObject(path="/bin/bar", mode="0755", uid="root", gid="bin")
    >>> assert __rpm_attr(fi) == "%attr(0755, -, bin)"
    """
    m = fo.permission()  # ex. "0755"

    try:
        u = fo.uid in (0, "root") and "-" or \
            pwd.getpwuid(fo.uid).pw_name

    except TypeError:  # It's not an integer such like 'bin'.
        u = fo.uid

    except KeyError:  # maybe fo.uid not in pwd database.
        u = "-"

    try:
        g = fo.gid in (0, "root") and "-" or \
            grp.getgrgid(fo.gid).gr_name

    except (TypeError, ValueError):  # It's not an integer.
        g = fo.gid

    except KeyError:  # likewise
        g = "-"

    return "%%attr(%(m)s, %(u)s, %(g)s)" % {"m": m, "u": u, "g": g}


def rpm_attr(fo):
    """
    Returns rpm_attr for given file objects.
    """
    try:
        rattr = getattr(fo, "rpm_attr", "")
    except KeyError:
        rattr = fo.get("rpm_attr", "")

    if not rattr:
        if fo.need_to_chmod() or fo.need_to_chown():
            rattr = __rpm_attr(fo) + " "

        if fo.type() == G.TYPE_DIR:
            rattr += "%dir "

    return rattr


def mock_dist():
    """
    Resolve the distributionn name from /etc/mock/defaults.cfg.
    """
    try:
        mock_cfg = os.path.realpath("/etc/mock/default.cfg")
        return os.path.splitext(os.path.split(mock_cfg)[-1])[0]
    except:
        return None


def rpm_header_from_rpmfile(rpmfile):
    """Read rpm.hdr from rpmfile.
    """
    return ts().hdrFromFdno(open(rpmfile, "rb"))


@U.memoize
def is_noarch(srpm):
    """Determine if given srpm is noarch (arch-independent).
    """
    return rpm_header_from_rpmfile(srpm)["arch"] == "noarch"


# vim:sw=4:ts=4:et:
