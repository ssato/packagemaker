#
# PackageMaker is a successor of xpack.py, a script to build packages from
# existing files on your system.
#
# It will try gathering the info of files, dirs and symlinks in given path
# list, and then:
#
# * arrange src tree contains these files, dirs and symlinks with these
#   relative path kept, and build files (Makefile.am, configure.ac, etc.)
#   to install these.
#
# * generate packaging metadata like RPM SPEC, debian/rules, etc.
#
# * build package such as rpm, src.rpm, deb, etc.
#
#
# NOTE: The permissions of the files might be lost during packaging. If you
# want to ensure these are saved or force set permissions as you wanted,
# specify these explicitly in Makefile.am or rpm spec, etc.
#
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
#
# Requirements:
# * rpmbuild in rpm-build package
# * python-cheetah: EPEL should be needed for RHEL (option: it's not needed if
#   you just want to setup src tree)
# * autotools: both autoconf and automake (option: see the above comment)
# * rpm-python
# * pyxattr (option; if you want to try with --use-pyxattr)
#
#
# TODO:
# * correct wrong English expressions
# * more complete tests
# * stabilize the API of the plugin system
# * sort out command line options: Work in progress
# * eliminate the strong dependency to rpm and make it runnable on debian based
#   systems (w/o rpm-python)
# * find causes of warnings during deb build and fix them all
# * keep permissions of targets in tar archives
#
#
# References (in random order):
# * http://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-creating-rpms.html
# * http://docs.fedoraproject.org/en-US/Fedora_Draft_Documentation/0.1/html/RPM_Guide/ch-rpm-programming-python.html
# * http://cdbs-doc.duckcorp.org
# * https://wiki.duckcorp.org/DebianPackagingTutorial/CDBS
# * http://kitenet.net/~joey/talks/debhelper/debhelper-slides.pdf
# * http://wiki.debian.org/IntroDebianPackaging
# * http://www.debian.org/doc/maint-guide/ch-dother.ja.html
#
#
# Alternatives:
# * buildrpm: http://magnusg.fedorapeople.org/buildrpm/
#
#
# Internal:
#
# Make some pylint errors ignored:
# pylint: disable=E0611
# pylint: disable=E1101
# pylint: disable=E1103
# pylint: disable=W0613
#
# How to run pylint: pylint --rcfile pylintrc pmaker.py
#

from distutils.sysconfig import get_python_lib
from itertools import count, groupby

import ConfigParser as cp
import cPickle as pickle
import copy
import datetime
import doctest
import glob
import grp
import inspect
import locale
import logging
import operator
import optparse
import os
import os.path
import platform
import pwd
import random
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest

import rpm


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
    UPTO = "build"
    CHEETAH_ENABLED = True

except ImportError:
    logging.warn("python-cheetah is not found. Packaging process can go up to \"setup\" step.")

    UPTO = "setup"
    CHEETAH_ENABLED = False

    def Template(*args, **kwargs):
        raise RuntimeError("python-cheetah is missing and cannot proceed any more.")


try:
    import xattr   # pyxattr
    PYXATTR_ENABLED = True

except ImportError:
    # Make up a "Null-Object" like class mimics xattr module.
    class xattr:
        @staticmethod
        def get_all(*args):
            return ()

        @staticmethod
        def set(*args):
            return ()

        # TODO: Older versions of python do not support decorator expressions
        # and should need the followings:
        #get_all = classmethod(get_all)
        #set = classmethod(set)
    
    PYXATTR_ENABLED = False


try:
    from hashlib import md5, sha1 #, sha256, sha512

except ImportError:  # python < 2.5
    from md5 import md5
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
    import json
    JSON_ENABLED = True

except ImportError:
    JSON_ENABLED = False

    class json:
        @staticmethod
        def load(*args):
            return ()


try:
    from yum import rpmsack
    YUM_ENABLED = True

except ImportError:
    YUM_ENABLED = False


__title__   = "packagemaker"
__version__ = "0.2"
__author__  = "Satoru SATOH"
__email__   = "satoru.satoh@gmail.com"
__website__ = "https://github.com/ssato/rpmkit"


FILEINFOS = {}
PACKAGE_MAKERS = {}
COLLECTORS = {}


COMPRESSORS = (
    # cmd, extension, am_option,
    ("xz",    "xz",  "no-dist-gzip dist-xz"),
    ("bzip2", "bz2", "no-dist-gzip dist-bzip2"),
    ("gzip",  "gz",  ""),
)


CONFLICTS_STATEDIR = "/var/lib/%(name)s-overrides"
CONFLICTS_SAVEDIR = os.path.join(CONFLICTS_STATEDIR, "saved")
CONFLICTS_NEWDIR = os.path.join(CONFLICTS_STATEDIR, "new")


TEMPLATES = {
    "configure.ac":
"""\
AC_INIT([$name],[$version])
AM_INIT_AUTOMAKE([${compressor.am_opt} foreign subdir-objects tar-pax])

dnl http://www.flameeyes.eu/autotools-mythbuster/automake/silent.html
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])

dnl TODO: fix autoconf macros used.
AC_PROG_LN_S
m4_ifdef([AC_PROG_MKDIR_P],[AC_PROG_MKDIR_P],[AC_SUBST([MKDIR_P],[mkdir -p])])
m4_ifdef([AC_PROG_SED],[AC_PROG_SED],[AC_SUBST([SED],[sed])])

dnl TODO: Is it better to generate ${name}.spec from ${name}.spec.in ?
AC_CONFIG_FILES([
Makefile
])

AC_OUTPUT
""",
    "Makefile.am":
"""\
#import os.path
EXTRA_DIST = MANIFEST MANIFEST.overrides
#if $conflicted_fileinfos
EXTRA_DIST += apply-overrides revert-overrides
#end if
#if $format == "rpm"
EXTRA_DIST += ${name}.spec rpm.mk

abs_srcdir  ?= .
include \$(abs_srcdir)/rpm.mk
#end if

#for $dd in $distdata
pkgdata${dd.id}dir = $dd.dir
dist_pkgdata${dd.id}_DATA = \\
#for $f in $dd.files
$f \\
#end for
\$(NULL)

#end for

#for $fi in $fileinfos
#if $fi.type() == "symlink"
#set $dir = os.path.dirname($fi.target)
#set $bn = os.path.basename($fi.target)
install-data-hook::
\t\$(AM_V_at)test -d \$(DESTDIR)$dir || \$(MKDIR_P) \$(DESTDIR)$dir
\t\$(AM_V_at)cd \$(DESTDIR)$dir && \$(LN_S) $fi.linkto $bn

#else
#if $fi.type() == "dir"
install-data-hook::
\t\$(AM_V_at)test -d \$(DESTDIR)$fi.target || \$(MKDIR_P) \$(DESTDIR)$fi.target

#end if
#end if
#end for

MKDIR_P ?= mkdir -p
SED ?= sed
""",
    "README":
"""\
This package provides some backup data collected on
$host by $packager at $date.date.
""",
    "MANIFEST":
"""\
#for $fi in $fileinfos
#if not $fi.conflicts
$fi.target
#end if
#end for
""",
    "MANIFEST.overrides":
"""\
#for $fi in $conflicted_fileinfos
$fi.target
#end for
""",
    "rpm.mk":
"""\
#raw
abs_builddir    ?= $(shell pwd)

rpmdir = $(abs_builddir)/rpm
rpmdirs = $(addprefix $(rpmdir)/,RPMS BUILD BUILDROOT)

rpmbuild = rpmbuild \
--quiet \
--define "_topdir $(rpmdir)" \
--define "_srcrpmdir $(abs_builddir)" \
--define "_sourcedir $(abs_builddir)" \
--define "_buildroot $(rpmdir)/BUILDROOT" \
$(NULL)

$(rpmdirs):
\t$(AM_V_at)$(MKDIR_P) $@

rpm srpm: $(PACKAGE).spec dist $(rpmdirs)

rpm:
\t$(AM_V_GEN)$(rpmbuild) -bb $<
\t$(AM_V_at)mv $(rpmdir)/RPMS/*/*.rpm $(abs_builddir)

srpm:
\t$(AM_V_GEN)$(rpmbuild) -bs $<

.PHONY: rpm srpm
#end raw
""",
    "package.spec":
"""\
%define  savedir  /var/lib/pmaker/preserved
%define  newdir  /var/lib/pmaker/installed

Name:           $name
Version:        $version
Release:        1%{?dist}
Summary:        $summary
Group:          $group
License:        $license
URL:            $url
Source0:        %{name}-%{version}.tar.${compressor.ext}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
#if $noarch
BuildArch:      noarch
#end if
#for $fi in $fileinfos
#if $fi.type() == "symlink"
#set $linkto = $fi.linkto
#BuildRequires:  $linkto
#end if
#end for
#for $rel in $relations
#set $rel_targets = ", ".join($rel.targets)
$rel.type:\t$rel_targets
#end for


%description
This package provides some backup data collected on
$host by $packager at $date.date.


#if $conflicted_fileinfos
%package        overrides
Summary:        Some more extra data override files owned by other packages
Group:          $group
Requires:       %{name} = %{version}-%{release}
#set $reqs = list(set([(fi.conflicts["name"], fi.conflicts["version"], fi.conflicts["release"]) for fi in $conflicted_fileinfos]))
#for $name, $version, $release in $reqs
Requires:       $name = ${version}-$release
#end for


%description    overrides
Some more extra data will override and replace other packages'.
#end if


%prep
%setup -q


%build
%configure --quiet --enable-silent-rules
make %{?_smp_mflags} V=0


%install
rm -rf \$RPM_BUILD_ROOT
make install DESTDIR=\$RPM_BUILD_ROOT

#if $conflicted_fileinfos
mkdir -p \$RPM_BUILD_ROOT$conflicts_savedir
mkdir -p \$RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
install -m 755 apply-overrides \$RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
install -m 755 revert-overrides \$RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
#end if


%clean
rm -rf \$RPM_BUILD_ROOT

$getVar("scriptlets", "")

#if $conflicted_fileinfos
%post           overrides
if [ $1 = 1 -o $1 = 2 ]; then    # install or update
    %{_libexecdir}/%{name}-overrides/apply-overrides
fi


%preun          overrides
if [ $1 = 0 ]; then    # uninstall (! update)
    %{_libexecdir}/%{name}-overrides/revert-overrides
fi
#end if


%files
%defattr(-,root,root,-)
%doc README
%doc MANIFEST
#for $fi in $not_conflicted_fileinfos
$fi.rpm_attr()$fi.target
#end for


#if $conflicted_fileinfos
%files          overrides
%defattr(-,root,root,-)
%doc MANIFEST.overrides
%dir $conflicts_savedir
%{_libexecdir}/%{name}-overrides/*-overrides
#for $fi in $conflicted_fileinfos
$fi.rpm_attr()$fi.target
#end for
#end if


%changelog
#if $changelog
$changelog
#else
* $date.timestamp ${packager} <${mail}> - ${version}-${release}
- Initial packaging.
#end if
""",
    "apply-overrides":
"""\
#! /bin/bash
set -e

#if $conflicted_fileinfos
files="
#for $fi in $conflicted_fileinfos
#if $fi.type() == "file"
$fi.original_path
#end if
#end for
"

for f in \$files
do
    dest=$conflicts_savedir\$f

#raw
    dir=$(dirname $dest)
    test -d $dir || mkdir -p $dir

    if test -f $dest; then
        csum1=$(sha1sum $f | cut -f 1 -d ' ')
        csum2=$(sha1sum $dest | cut -f 1 -d ' ')

        if test "x$csum1" = "x$csum2"; then
            echo "[Info] Looks already saved. Skip it: $f"
        else
            echo "[Info] Overwrite priviously saved one: $f"
            cp -af $f $dest
        fi
    else
        echo "[Debug] Saving: $f"
        cp -a $f $dest
    fi
#end raw
done
#else
# No conflicts and nothing to do:
exit 0
#end if
""",
    "revert-overrides":
"""\
#! /bin/bash
set -e

#if $conflicted_fileinfos
files="
#for $fi in $conflicted_fileinfos
#if $fi.type() == "file"
$fi.original_path
#end if
#end for
"

for f in \$files
do
    backup=$conflicts_savedir\$f

#raw
    csum1=$(sha1sum $f | cut -f 1 -d ' ')
    csum2=$(sha1sum $backup | cut -f 1 -d ' ')

    if test "x$csum1" = "x$csum2"; then
        echo "[Info] Looks already backed up. Skip it: $f"
    else
        echo "[Info] Restore from backup: $f"
        cp -af $backup $f
    fi
#end raw
done
#else
# No conflicts and nothing to do:
exit 0
#end if
""",
    "debian/control":
"""\
Source: $name
Priority: optional
Maintainer: $packager <$mail>
Build-Depends: debhelper (>= 7.3.8), autotools-dev
Standards-Version: 3.9.0
Homepage: $url

Package: $name
Section: database
#if $noarch
Architecture: all
#else
Architecture: any
#end if
#set $requires_list = ""
#for $rel in $relations
#if $rel.targets
#set $rel_targets = ", ".join($rel.targets)
#end if
#if $rel.type == "Depends"
#set $requires_list += $rel_targets
#end if
#end for
Depends: \${shlibs:Depends}, \${misc:Depends}$requires_list
Description: $summary
  $summary
""",
    "debian/rules":
"""\
#raw
#!/usr/bin/make -f
%:
\tdh $@

override_dh_builddeb:
\tdh_builddeb -- -Zbzip2
#end raw
""",
    "debian/dirs":
"""\
#for $fi in $fileinfos
#if $fi.type == "dir"
#set $dir = $fi.target[1:]
$dir
#end if
#end for
""",
    "debian/compat":
"""\
7
""",
    "debian/source/format":
"""\
3.0 (native)
""",
    "debian/source/options":
"""\
# Use bzip2 instead of gzip
compression = "bzip2"
compression-level = 9
""",
    "debian/copyright":
"""\
This package was debianized by $packager <$mail>
on $date.date.

This package is distributed under $license.
""",
    "debian/changelog":
"""\
#if $changelog
$changelog
#else
$name ($version) unstable; urgency=low

  * New upstream release

 -- $packager <$mail>  $date.date
#end if
""",
}


EXAMPLE_LOGS = [
    """## A. Packaing files in given files list, "files.list":

$ cat << EOF > files.list
> /etc/auto.*
> /etc/modprobe.d/*
> /etc/resolv.conf
> /etc/yum.repos.d/fedora.repo
> #/etc/aliases.db
> /etc/system-release
> /etc/httpd/conf.d
> EOF
$ python pmaker.py -n sysdata -w ./0 -q files.list
21:34:57 [WARNING] /etc/auto.iso is owned by miniascape
21:34:58 [WARNING] /etc/auto.master is owned by autofs
21:34:58 [WARNING] /etc/auto.misc is owned by autofs
21:34:58 [WARNING] /etc/auto.net is owned by autofs
21:34:58 [WARNING] /etc/auto.smb is owned by autofs
21:34:58 [WARNING] /etc/httpd/conf.d is owned by httpd
21:34:58 [WARNING] /etc/modprobe.d/blacklist-visor.conf is owned by pilot-link
21:34:58 [WARNING] /etc/modprobe.d/blacklist.conf is owned by hwdata
21:34:58 [WARNING] /etc/modprobe.d/dist-alsa.conf is owned by module-init-tools
21:34:58 [WARNING] /etc/modprobe.d/dist-oss.conf is owned by module-init-tools
21:34:58 [WARNING] /etc/modprobe.d/dist.conf is owned by module-init-tools
21:34:58 [WARNING] /etc/modprobe.d/libmlx4.conf is owned by libmlx4
21:34:58 [WARNING] /etc/system-release is owned by fedora-release
21:34:58 [WARNING] /etc/yum.repos.d/fedora.repo is owned by fedora-release
21:34:58 [WARNING] [Errno 1] Operation not permitted: '/tmp/w/0/sysdata-0.1/src/etc/httpd/conf.d'
configure.ac:2: installing `./install-sh'
    ... snip ...
  GEN    srpm
$ ls 0
sysdata-0.1
$ ls -w 80 0/sysdata-0.1/
MANIFEST            pmaker-build.stamp
MANIFEST.overrides  pmaker-configure.stamp
Makefile            pmaker-package-filelist.pkl
Makefile.am         pmaker-preconfigure.stamp
Makefile.in         pmaker-sbuild.stamp
README              pmaker-setup.stamp
aclocal.m4          rpm
autom4te.cache      rpm.mk
config.log          src
config.status       sysdata-0.1-1.fc14.noarch.rpm
configure           sysdata-0.1-1.fc14.src.rpm
configure.ac        sysdata-0.1.tar.bz2
install-sh          sysdata-overrides-0.1-1.fc14.noarch.rpm
missing             sysdata.spec
$ rpm -qlp 0/sysdata-0.1/sysdata-0.1-1.fc14.noarch.rpm
/etc/auto.iso.rpmsave
/etc/auto.iso.save
/etc/auto.master.save
/etc/resolv.conf
/usr/share/doc/sysdata-0.1
/usr/share/doc/sysdata-0.1/MANIFEST
/usr/share/doc/sysdata-0.1/README
$ rpm -qlp 0/sysdata-0.1/sysdata-overrides-0.1-1.fc14.noarch.rpm
/etc/auto.iso
/etc/auto.master
/etc/auto.misc
/etc/auto.net
/etc/auto.smb
/etc/httpd/conf.d
/etc/modprobe.d/blacklist-visor.conf
/etc/modprobe.d/blacklist.conf
/etc/modprobe.d/dist-alsa.conf
/etc/modprobe.d/dist-oss.conf
/etc/modprobe.d/dist.conf
/etc/modprobe.d/libmlx4.conf
/etc/system-release
/etc/yum.repos.d/fedora.repo
/usr/share/doc/sysdata-overrides-0.1
/usr/share/doc/sysdata-overrides-0.1/MANIFEST.overrides
$
""",
    """\
## B. Same as above except that files list is read from stdin and mock
## is not used for building rpms:

$ cat files.list | python pmaker.py -n sysdata -w ./1 -q --no-mock -
21:47:34 [WARNING] /etc/auto.iso is owned by miniascape
21:47:34 [WARNING] /etc/auto.master is owned by autofs
21:47:34 [WARNING] /etc/auto.misc is owned by autofs
21:47:34 [WARNING] /etc/auto.net is owned by autofs
    ... snip ...
  GEN    srpm
{ test ! -d "sysdata-0.1" || { find "sysdata-0.1" -type d ! -perm -200 -exec chmod u+w {} ';' && rm -fr "sysdata-0.1"; }; }
test -d "sysdata-0.1" || mkdir "sysdata-0.1"
test -n "" \
|| find "sysdata-0.1" -type d ! -perm -755 \
        -exec chmod u+rwx,go+rx {} \; -o \
  ! -type d ! -perm -444 -links 1 -exec chmod a+r {} \; -o \
  ! -type d ! -perm -400 -exec chmod a+r {} \; -o \
  ! -type d ! -perm -444 -exec /bin/sh /tmp/w/1/sysdata-0.1/install-sh -c -m a+r {} {} \; \
|| chmod -R a+r "sysdata-0.1"
tardir=sysdata-0.1 && /bin/sh /tmp/w/1/sysdata-0.1/missing --run tar chof - "$tardir" | bzip2 -9 -c >sysdata-0.1.tar.bz2
{ test ! -d "sysdata-0.1" || { find "sysdata-0.1" -type d ! -perm -200 -exec chmod u+w {} ';' && rm -fr "sysdata-0.1"; }; }
  GEN    rpm
configure: WARNING: unrecognized options: --disable-dependency-tracking
configure: WARNING: unrecognized options: --disable-dependency-tracking
$ ls -w 80 1/sysdata-0.1/
MANIFEST            pmaker-build.stamp
MANIFEST.overrides  pmaker-configure.stamp
Makefile            pmaker-package-filelist.pkl
Makefile.am         pmaker-preconfigure.stamp
Makefile.in         pmaker-sbuild.stamp
README              pmaker-setup.stamp
aclocal.m4          rpm
autom4te.cache      rpm.mk
config.log          src
config.status       sysdata-0.1-1.fc14.noarch.rpm
configure           sysdata-0.1-1.fc14.src.rpm
configure.ac        sysdata-0.1.tar.bz2
install-sh          sysdata-overrides-0.1-1.fc14.noarch.rpm
missing             sysdata.spec
$ rpm -qlp 1/sysdata-0.1/sysdata-0.1-1.fc14.noarch.rpm
/etc/auto.iso.rpmsave
/etc/auto.iso.save
/etc/auto.master.save
/etc/resolv.conf
/usr/share/doc/sysdata-0.1
/usr/share/doc/sysdata-0.1/MANIFEST
/usr/share/doc/sysdata-0.1/README
$ rpm -qlp 1/sysdata-0.1/sysdata-overrides-0.1-1.fc14.noarch.rpm
/etc/auto.iso
/etc/auto.master
/etc/auto.misc
/etc/auto.net
/etc/auto.smb
/etc/httpd/conf.d
/etc/modprobe.d/blacklist-visor.conf
/etc/modprobe.d/blacklist.conf
/etc/modprobe.d/dist-alsa.conf
/etc/modprobe.d/dist-oss.conf
/etc/modprobe.d/dist.conf
/etc/modprobe.d/libmlx4.conf
/etc/system-release
/etc/yum.repos.d/fedora.repo
/usr/share/doc/sysdata-overrides-0.1
/usr/share/doc/sysdata-overrides-0.1/MANIFEST.overrides
$
""",
    """## C. Packaing single file, /etc/resolve.conf:

$ echo /etc/resolv.conf | python pmaker.py -n resolvconf -w 2 --debug -
21:51:43 [INFO] Use PackageMaker: RpmPackageMaker: type=filelist, format=rpm
21:51:43 [INFO] Use Collector: FilelistCollector (filelist)
21:51:43 [INFO] Setting up src tree in /tmp/w/2/resolvconf-0.1: resolvconf
21:51:43 [DEBUG]  Creating a directory: /tmp/w/2/resolvconf-0.1
21:51:43 [DEBUG]  Creating a directory: /tmp/w/2/resolvconf-0.1/src
21:51:43 [DEBUG]  Copying from '/etc/resolv.conf' to '/tmp/w/2/resolvconf-0.1/src/etc/resolv.conf'
21:51:43 [INFO]  Run: touch /tmp/w/2/resolvconf-0.1/pmaker-setup.stamp [/tmp/w/2/resolvconf-0.1]
21:51:43 [INFO] Arrange autotool-ized src directory: resolvconf
21:51:43 [INFO]  Run: touch /tmp/w/2/resolvconf-0.1/pmaker-preconfigure.stamp [/tmp/w/2/resolvconf-0.1]
21:51:43 [INFO] Configuring src distribution: resolvconf
21:51:43 [INFO]  Run: autoreconf -vfi [/tmp/w/2/resolvconf-0.1]
autoreconf: Entering directory `.'
autoreconf: configure.ac: not using Gettext
autoreconf: running: aclocal --force
autoreconf: configure.ac: tracing
autoreconf: configure.ac: not using Libtool
autoreconf: running: /usr/bin/autoconf --force
autoreconf: configure.ac: not using Autoheader
autoreconf: running: automake --add-missing --copy --force-missing
configure.ac:2: installing `./install-sh'
configure.ac:2: installing `./missing'
autoreconf: Leaving directory `.'
21:51:46 [INFO]  Run: touch /tmp/w/2/resolvconf-0.1/pmaker-configure.stamp [/tmp/w/2/resolvconf-0.1]
21:51:46 [INFO] Building src package: resolvconf
21:51:46 [INFO]  Run: ./configure --quiet [/tmp/w/2/resolvconf-0.1]
21:51:48 [INFO]  Run: make [/tmp/w/2/resolvconf-0.1]
21:51:48 [INFO]  Run: make dist [/tmp/w/2/resolvconf-0.1]
21:51:48 [INFO]  Run: make srpm [/tmp/w/2/resolvconf-0.1]
21:51:48 [INFO]  Run: touch /tmp/w/2/resolvconf-0.1/pmaker-sbuild.stamp [/tmp/w/2/resolvconf-0.1]
21:51:48 [INFO] Building bin packages: resolvconf
21:51:48 [INFO]  Run: mock --version > /dev/null [/tmp/w/2/resolvconf-0.1]
21:51:49 [DEBUG]  Run: rpm -q --specfile --qf "%{n}-%{v}-%{r}.src.rpm
" /tmp/w/2/resolvconf-0.1/resolvconf.spec [.]
21:51:49 [INFO]  Run: mock -r fedora-14-x86_64 resolvconf-0.1-1.fc14.src.rpm --quiet [/tmp/w/2/resolvconf-0.1]
21:52:17 [INFO]  Run: mv /var/lib/mock/fedora-14-x86_64/result/*.rpm /tmp/w/2/resolvconf-0.1 [/tmp/w/2/resolvconf-0.1]
21:52:17 [INFO]  Run: touch /tmp/w/2/resolvconf-0.1/pmaker-build.stamp [/tmp/w/2/resolvconf-0.1]
21:52:17 [INFO] Successfully created packages in /tmp/w/2/resolvconf-0.1: resolvconf
$ rpm -qlp 2/resolvconf-0.1/resolvconf-0.1-1.fc14.noarch.rpm
/etc/resolv.conf
/usr/share/doc/resolvconf-0.1
/usr/share/doc/resolvconf-0.1/MANIFEST
/usr/share/doc/resolvconf-0.1/README
$
""",
    """\
## D. Packaing single file, 3/rhel-server-5.6-i386-dvd.iso,
## will be installed into /srv/isos/:

$ isoname=rhel-server-5.6-i386-dvd.iso
$ echo "3/$isoname,target=/srv/isos/$isoname,uid=0,gid=0" | \
> python pmaker.py --itype filelist.ext -n rhel-server-5-6-i386-dvd-iso \
> -w 3 --upto build --no-rpmdb --no-mock -v -
21:56:29 [INFO] Use PackageMaker: RpmPackageMaker: type=filelist, format=rpm
21:56:29 [INFO] Use Collector: ExtFilelistCollector (filelist.ext)
21:56:29 [INFO] Setting up src tree in /tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1: rhel-server-5-6-i386-dvd-iso
21:56:29 [INFO] Override attr gid=0 in fileinfo: path=3/rhel-server-5.6-i386-dvd.iso
21:56:29 [INFO] Override attr target=/srv/isos/rhel-server-5.6-i386-dvd.iso in fileinfo: path=3/rhel-server-5.6-i386-dvd.iso
21:56:29 [INFO] Override attr uid=0 in fileinfo: path=3/rhel-server-5.6-i386-dvd.iso
21:56:29 [INFO]  Run: touch /tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1/pmaker-setup.stamp [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:29 [INFO] Arrange autotool-ized src directory: rhel-server-5-6-i386-dvd-iso
21:56:29 [INFO]  Run: touch /tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1/pmaker-preconfigure.stamp [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:29 [INFO] Configuring src distribution: rhel-server-5-6-i386-dvd-iso
21:56:29 [INFO]  Run: autoreconf -fi [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
configure.ac:2: installing `./install-sh'
configure.ac:2: installing `./missing'
21:56:32 [INFO]  Run: touch /tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1/pmaker-configure.stamp [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:32 [INFO] Building src package: rhel-server-5-6-i386-dvd-iso
21:56:32 [INFO]  Run: ./configure --quiet --enable-silent-rules [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:34 [INFO]  Run: make V=0 > /dev/null [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:34 [INFO]  Run: make dist V=0 > /dev/null [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:34 [INFO]  Run: make srpm [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:34 [INFO]  Run: touch /tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1/pmaker-sbuild.stamp [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:34 [INFO] Building bin packages: rhel-server-5-6-i386-dvd-iso
21:56:34 [INFO]  Run: make rpm [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
configure: WARNING: unrecognized options: --disable-dependency-tracking
configure: WARNING: unrecognized options: --disable-dependency-tracking
21:56:37 [INFO]  Run: touch /tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1/pmaker-build.stamp [/tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1]
21:56:37 [INFO] Successfully created packages in /tmp/w/3/rhel-server-5-6-i386-dvd-iso-0.1: rhel-server-5-6-i386-dvd-iso
$ rpm -qlp 3/rhel-server-5-6-i386-dvd-iso-0.1/rhel-server-5-6-i386-dvd-iso-0.1-1.fc14.noarch.rpm
/srv/isos/rhel-server-5.6-i386-dvd.iso
/usr/share/doc/rhel-server-5-6-i386-dvd-iso-0.1
/usr/share/doc/rhel-server-5-6-i386-dvd-iso-0.1/MANIFEST
/usr/share/doc/rhel-server-5-6-i386-dvd-iso-0.1/README
$
""",
    """## E. Packaging itself:

$ python pmaker.py --build-self
Listing . ...
Compiling ./__init__.py ...
configure.ac:2: installing `./install-sh'
configure.ac:2: installing `./missing'
{ test ! -d "packagemaker-0.2.20110502" || { find "packagemaker-0.2.20110502" -type d ! -perm -200 -exec chmod u+w {} ';' && rm -fr "packagemaker-0.2.20110502"; }; }
test -d "packagemaker-0.2.20110502" || mkdir "packagemaker-0.2.20110502"
test -n "" \
|| find "packagemaker-0.2.20110502" -type d ! -perm -755 \
        -exec chmod u+rwx,go+rx {} \; -o \
  ! -type d ! -perm -444 -links 1 -exec chmod a+r {} \; -o \
  ! -type d ! -perm -400 -exec chmod a+r {} \; -o \
  ! -type d ! -perm -444 -exec /bin/sh /tmp/pm-IzL80r/packagemaker-0.2.20110502/install-sh -c -m a+r {} {} \; \
|| chmod -R a+r "packagemaker-0.2.20110502"
tardir=packagemaker-0.2.20110502 && /bin/sh /tmp/pm-IzL80r/packagemaker-0.2.20110502/missing --run tar chof - "$tardir" | bzip2 -9 -c >packagemaker-0.2.20110502.tar.bz2
{ test ! -d "packagemaker-0.2.20110502" || { find "packagemaker-0.2.20110502" -type d ! -perm -200 -exec chmod u+w {} ';' && rm -fr "packagemaker-0.2.20110502"; }; }
  GEN    srpm
$ ls -w 80 /tmp/pm-IzL80r/packagemaker-0.2.20110502/
MANIFEST            packagemaker-0.2.20110502-1.fc14.noarch.rpm
MANIFEST.overrides  packagemaker-0.2.20110502-1.fc14.src.rpm
Makefile            packagemaker-0.2.20110502.tar.bz2
Makefile.am         packagemaker.spec
Makefile.in         pmaker-build.stamp
README              pmaker-configure.stamp
aclocal.m4          pmaker-package-filelist.pkl
autom4te.cache      pmaker-preconfigure.stamp
config.log          pmaker-sbuild.stamp
config.status       pmaker-setup.stamp
configure           rpm
configure.ac        rpm.mk
install-sh          src
missing
$ rpm -qlp /tmp/pm-IzL80r/packagemaker-0.2.20110502/packagemaker-0.2.20110502-1.fc14.noarch.rpm
/usr/bin/pmaker
/usr/lib/python2.7/site-packages/pmaker/__init__.py
/usr/lib/python2.7/site-packages/pmaker/__init__.pyc
/usr/lib/python2.7/site-packages/pmaker/__init__.pyo
/usr/share/doc/packagemaker-0.2.20110502
/usr/share/doc/packagemaker-0.2.20110502/MANIFEST
/usr/share/doc/packagemaker-0.2.20110502/README
$ sed -n "/^%files/,/^$/p" /tmp/pm-IzL80r/packagemaker-0.2.20110502/packagemaker.spec 
%files
%defattr(-,root,root,-)
%doc README
%doc MANIFEST
%attr(0755, -, -) /usr/bin/pmaker
/usr/lib/python2.7/site-packages/pmaker/__init__.py
/usr/lib/python2.7/site-packages/pmaker/__init__.pyc
/usr/lib/python2.7/site-packages/pmaker/__init__.pyo

$
""",
    """## F. Packaging files under /etc which is not owned by any RPMs:

$ list_files () { dir=$1; sudo find $dir -type f; }                                                                                                            $ is_not_from_rpm () { f=$1; LANG=C sudo rpm -qf $f | grep -q 'is not owned' 2>/dev/null; }
$ (for f in `list_files /etc`; do is_not_from_rpm $f && echo $f; done) \\
>  > etc.not_from_package.files
$ sudo python pmaker.py -n etcdata --pversion $(date +%Y%m%d) \\
> --debug -w etcdata-build etc.not_from_package.files
[sudo] password for ssato:
14:15:03 [DEBUG]  Could load the cache: /root/.cache/pmaker.rpm.filelist.pkl
14:15:09 [INFO] Setting up src tree in /tmp/t/etcdata-build/etcdata-20110217: etcdata
14:15:09 [DEBUG]  Creating a directory: /tmp/t/etcdata-build/etcdata-20110217
...(snip)...
14:16:33 [INFO] Successfully created packages in /tmp/t/etcdata-build/etcdata-20110217: etcdata
$ sudo chown -R ssato.ssato etcdata-build/
$ ls etcdata-build/etcdata-20110217/
MANIFEST            Makefile.am  aclocal.m4      config.status  etcdata-20110217-1.fc14.src.rpm  etcdata.spec  rpm
MANIFEST.overrides  Makefile.in  autom4te.cache  configure      etcdata-20110217.tar.bz2         install-sh    rpm.mk
Makefile            README       config.log      configure.ac   etcdata-20110217.tar.gz          missing       src
$ sudo make -C etcdata-build/etcdata-20110217/ rpm
...(snip)...
$ rpm -qlp etcdata-build/etcdata-20110217/etcdata-20110217-1.fc14.noarch.rpm
/etc/.pwd.lock
/etc/X11/xorg.conf
/etc/X11/xorg.conf.by-psb-config-display
/etc/X11/xorg.conf.d/01-poulsbo.conf
/etc/X11/xorg.conf.livna-config-backup
/etc/aliases.db
/etc/crypttab
/etc/gconf/gconf.xml.defaults/%gconf-tree-af.xml
...(snip)...
/etc/yum.repos.d/fedora-chromium.repo
/usr/share/doc/etcdata-20110217
/usr/share/doc/etcdata-20110217/MANIFEST
/usr/share/doc/etcdata-20110217/README
$
""",
    """## G. Packaging single file on RHEL 5 host and build it on fedora 14 host:

$ ssh builder@rhel-5-6-vm-0
builder@rhel-5-6-vm-0's password:
[builder@rhel-5-6-vm-0 ~]$ cat /etc/redhat-release
Red Hat Enterprise Linux Server release 5.6 (Tikanga)
[builder@rhel-5-6-vm-0 ~]$ curl -s https://github.com/ssato/rpmkit/raw/master/pmaker.py > pmaker
[builder@rhel-5-6-vm-0 ~]$ echo /etc/puppet/manifests/site.pp | \\
> python pmaker -n puppet-manifests -w 0 --debug --upto setup -
WARNING:root:python-cheetah is not found so that packaging process will go up to only 'setup' step.
19:42:48 [INFO] Setting up src tree in /home/builder/0/puppet-manifests-0.1: puppet-manifests
19:42:50 [DEBUG]  Could save the cache: /home/builder/.cache/pmaker.rpm.filelist.pkl
19:42:50 [DEBUG]  Creating a directory: /home/builder/0/puppet-manifests-0.1
19:42:50 [DEBUG]  Creating a directory: /home/builder/0/puppet-manifests-0.1/src
19:42:50 [DEBUG]  Copying from '/etc/puppet/manifests/site.pp' to '/home/builder/0/puppet-manifests-0.1/src/etc/puppet/manifests/site.pp'
19:42:50 [DEBUG]  Run: cp -a /etc/puppet/manifests/site.pp /home/builder/0/puppet-manifests-0.1/src/etc/puppet/manifests/site.pp [/home/builder]
19:42:50 [DEBUG]  Run: touch /home/builder/0/puppet-manifests-0.1/pmaker-setup.stamp [/home/builder/0/puppet-manifests-0.1]
[builder@rhel-5-6-vm-0 ~]$ tar jcvf puppet-manifests-0.1.tar.bz2 0/puppet-manifests-0.1/
0/puppet-manifests-0.1/
0/puppet-manifests-0.1/pmaker-setup.stamp
0/puppet-manifests-0.1/pmaker-package-filelist.pkl
0/puppet-manifests-0.1/src/
0/puppet-manifests-0.1/src/etc/
0/puppet-manifests-0.1/src/etc/puppet/
0/puppet-manifests-0.1/src/etc/puppet/manifests/
0/puppet-manifests-0.1/src/etc/puppet/manifests/site.pp
[builder@rhel-5-6-vm-0 ~]$ ls
0  puppet-manifests-0.1.tar.bz2  rpms  pmaker
[builder@rhel-5-6-vm-0 ~]$ ^D
$ cat /etc/fedora-release
Fedora release 14 (Laughlin)
$ scp builder@rhel-5-6-vm-0:~/puppet-manifests-0.1.tar.bz2 ./
builder@rhel-5-6-vm-0's password:
puppet-manifests-0.1.tar.bz2                 100%  722     0.7KB/s   00:00
$ tar jxvf puppet-manifests-0.1.tar.bz2
0/puppet-manifests-0.1/
0/puppet-manifests-0.1/pmaker-setup.stamp
0/puppet-manifests-0.1/pmaker-package-filelist.pkl
0/puppet-manifests-0.1/src/
0/puppet-manifests-0.1/src/etc/
0/puppet-manifests-0.1/src/etc/puppet/
0/puppet-manifests-0.1/src/etc/puppet/manifests/
0/puppet-manifests-0.1/src/etc/puppet/manifests/site.pp
$ echo /etc/puppet/manifests/site.pp | \\
> python pmaker.py -n puppet-manifests -w 0 --upto build \\
> --dist epel-5-i386 --debug -
05:27:55 [INFO] Setting up src tree in /tmp/w/0/puppet-manifests-0.1: puppet-manifests
05:27:55 [INFO] ...It looks already done. Skip the step: setup
05:27:55 [INFO] Configuring src distribution: puppet-manifests
05:27:55 [DEBUG]  Run: autoreconf -fi [/tmp/w/0/puppet-manifests-0.1]
05:27:58 [DEBUG]  Run: touch /tmp/w/0/puppet-manifests-0.1/pmaker-configure.stamp [/tmp/w/0/puppet-manifests-0.1]
05:27:58 [INFO] Building src package: puppet-manifests
05:27:58 [DEBUG]  Run: ./configure [/tmp/w/0/puppet-manifests-0.1]
05:27:59 [DEBUG]  Run: make dist [/tmp/w/0/puppet-manifests-0.1]
05:28:00 [DEBUG]  Run: make srpm [/tmp/w/0/puppet-manifests-0.1]
05:28:00 [DEBUG]  Run: touch /tmp/w/0/puppet-manifests-0.1/pmaker-sbuild.stamp [/tmp/w/0/puppet-manifests-0.1]
05:28:00 [INFO] Building bin packages: puppet-manifests
05:28:00 [DEBUG]  Run: mock --version > /dev/null [/tmp/w/0/puppet-manifests-0.1]
05:28:00 [DEBUG]  Run: mock -r epel-5-i386 puppet-manifests-0.1-1.*.src.rpm [/tmp/w/0/puppet-manifests-0.1]
05:28:59 [DEBUG]  Run: mv /var/lib/mock/epel-5-i386/result/*.rpm /tmp/w/0/puppet-manifests-0.1 [/tmp/w/0/puppet-manifests-0.1]
05:28:59 [DEBUG]  Run: touch /tmp/w/0/puppet-manifests-0.1/pmaker-build.stamp [/tmp/w/0/puppet-manifests-0.1]
05:28:59 [INFO] Successfully created packages in /tmp/w/0/puppet-manifests-0.1: puppet-manifests
$ rpm -qlp 0/puppet-manifests-0.1/puppet-manifests-0.1-1.^I
puppet-manifests-0.1-1.el5.noarch.rpm  puppet-manifests-0.1-1.el5.src.rpm  puppet-manifests-0.1-1.fc14.src.rpm
$ rpm -qlp 0/puppet-manifests-0.1/puppet-manifests-0.1-1.el5.noarch.rpm
/etc/puppet/manifests/site.pp
/usr/share/doc/puppet-manifests-0.1
/usr/share/doc/puppet-manifests-0.1/MANIFEST
/usr/share/doc/puppet-manifests-0.1/README
$
""",
    """## H. Packaging single file on debian host:

# echo /etc/resolv.conf | ./pmaker.py -n resolvconf -w w --format deb -
13:11:59 [WARNING] get_email: 'module' object has no attribute 'check_output'
13:11:59 [WARNING] get_fullname: 'module' object has no attribute 'check_output'
configure.ac:2: installing `./install-sh'
configure.ac:2: installing `./missing'
dh binary
   dh_testdir
   dh_auto_configure
configure: WARNING: unrecognized options: --disable-maintainer-mode, --disable-dependency-tracking
checking for a BSD-compatible install... /usr/bin/install -c
checking whether build environment is sane... yes
checking for a thread-safe mkdir -p... /bin/mkdir -p
checking for gawk... no
checking for mawk... mawk
checking whether make sets $(MAKE)... yes
checking whether ln -s works... yes
checking for a sed that does not truncate output... /bin/sed
configure: creating ./config.status
config.status: creating Makefile
configure: WARNING: unrecognized options: --disable-maintainer-mode, --disable-dependency-tracking
   dh_auto_build
make[1]: Entering directory `/root/w/resolvconf-0.1'
make[1]: Nothing to be done for `all'.
make[1]: Leaving directory `/root/w/resolvconf-0.1'
   dh_auto_test
   dh_testroot
   dh_prep
   dh_installdirs
   dh_auto_install
make[1]: Entering directory `/root/w/resolvconf-0.1'
make[2]: Entering directory `/root/w/resolvconf-0.1'
make[2]: Nothing to be done for `install-exec-am'.
test -z "/etc" || /bin/mkdir -p "/root/w/resolvconf-0.1/debian/resolvconf/etc"
 /usr/bin/install -c -m 644 src/etc/resolv.conf '/root/w/resolvconf-0.1/debian/resolvconf/etc'
make[2]: Leaving directory `/root/w/resolvconf-0.1'
make[1]: Leaving directory `/root/w/resolvconf-0.1'
   dh_install
   dh_installdocs
   dh_installchangelogs
   dh_installexamples
   dh_installman
   dh_installcatalogs
   dh_installcron
   dh_installdebconf
   dh_installemacsen
   dh_installifupdown
   dh_installinfo
   dh_pysupport
   dh_installinit
   dh_installmenu
   dh_installmime
   dh_installmodules
   dh_installlogcheck
   dh_installlogrotate
   dh_installpam
   dh_installppp
   dh_installudev
   dh_installwm
   dh_installxfonts
   dh_bugfiles
   dh_lintian
   dh_gconf
   dh_icons
   dh_perl
   dh_usrlocal
   dh_link
   dh_compress
   dh_fixperms
   dh_strip
   dh_makeshlibs
   dh_shlibdeps
   dh_installdeb
   dh_gencontrol
dpkg-gencontrol: warning: Depends field of package resolvconf: unknown substitution variable ${shlibs:Depends}
   dh_md5sums
   debian/rules override_dh_builddeb
make[1]: Entering directory `/root/w/resolvconf-0.1'
dh_builddeb -- -Zbzip2
dpkg-deb: building package `resolvconf' in `../resolvconf_0.1_all.deb'.
make[1]: Leaving directory `/root/w/resolvconf-0.1'
#
""",
    """\
## I. Packaging files with some attributes specified in JSON data:

$ cat filelist.json
[
    {
        "path": "/etc/resolv.conf",
        "target": {
            "target": "/var/lib/network/resolv.conf",
            "uid": 0,
            "gid": 0,
            "conflicts": "NetworkManager"
        }
    },
    {
        "path": "/etc/hosts",
        "target": {
            "conflicts": "setup",
            "rpmattr": "%config(noreplace)"
        }
    }
]
$ python pmaker.py --itype filelist.json -n netdata -w 5 -q filelist.json
01:03:01 [WARNING] /etc/hosts is owned by setup
configure.ac:2: installing `./install-sh'
configure.ac:2: installing `./missing'
{ test ! -d "netdata-0.1" || { find "netdata-0.1" -type d ! -perm -200 -exec chmod u+w {} ';' && rm -fr "netdata-0.1"; }; }
test -d "netdata-0.1" || mkdir "netdata-0.1"
test -n "" \
|| find "netdata-0.1" -type d ! -perm -755 \
        -exec chmod u+rwx,go+rx {} \; -o \
  ! -type d ! -perm -444 -links 1 -exec chmod a+r {} \; -o \
  ! -type d ! -perm -400 -exec chmod a+r {} \; -o \
  ! -type d ! -perm -444 -exec /bin/sh /tmp/0/5/netdata-0.1/install-sh -c -m a+r {} {} \; \
|| chmod -R a+r "netdata-0.1"
tardir=netdata-0.1 && /bin/sh /tmp/0/5/netdata-0.1/missing --run tar chof - "$tardir" | bzip2 -9 -c >netdata-0.1.tar.bz2
{ test ! -d "netdata-0.1" || { find "netdata-0.1" -type d ! -perm -200 -exec chmod u+w {} ';' && rm -fr "netdata-0.1"; }; }
  GEN    srpm
$ ls -w 80 5/netdata-0.1/
MANIFEST            netdata-0.1-1.fc14.noarch.rpm
MANIFEST.overrides  netdata-0.1-1.fc14.src.rpm
Makefile            netdata-0.1.tar.bz2
Makefile.am         netdata-overrides-0.1-1.fc14.noarch.rpm
Makefile.in         netdata.spec
README              pmaker-build.stamp
aclocal.m4          pmaker-configure.stamp
autom4te.cache      pmaker-package-filelist.pkl
config.log          pmaker-preconfigure.stamp
config.status       pmaker-sbuild.stamp
configure           pmaker-setup.stamp
configure.ac        rpm
install-sh          rpm.mk
missing             src
$ rpm -qlp 5/netdata-0.1/netdata-0.1-1.fc14.noarch.rpm
/usr/share/doc/netdata-0.1
/usr/share/doc/netdata-0.1/MANIFEST
/usr/share/doc/netdata-0.1/README
$ rpm -qlp 5/netdata-0.1/netdata-overrides-0.1-1.fc14.noarch.rpm
/etc/hosts
/usr/share/doc/netdata-overrides-0.1
/usr/share/doc/netdata-overrides-0.1/MANIFEST.overrides
/var/lib/network/resolv.conf
$

""",
]


EXAMPLE_RC = """\
#
# This is a configuration file example for pmaker.py
#
# Read the output of `pmaker.py --help` and edit the followings as needed.
#
[DEFAULT]
# working directory in absolute path:
workdir =

# packaging process will go up to this step:
upto    = build

# package format:
format  = rpm

# the tool to compress collected data archive. choices are xz, bz2 or gz:
compressor = bz2

# flags to control logging levels:
debug   = False
quiet   = False

# set to True if owners of target objects are ignored during packaging process:
ignore_owner    = False

# destination directory to be stripped from installed path in absolute path:
destdir =

# advanced option to be enabled if you want to use pyxattr to get extended
# attributes of target files, dirs and symlinks:
with_pyxattr    = False


## package:
# name of the package:
name    = pmade-data

# version of the package:
pversion = 0.1

# group of the package:
group   = System Environment/Base

# license of the package
license = GPLv2+

# url of the package to provide information:
url     = http://localhost.localdomain

# summary (short description) of the package:
summary =

# Does the package depend on architecture?:
arch    = False

# Full name of the packager, ex. John Doe
packager =

# Mail address of the packager
mail    =


## rpm:
# build target distribution will be used for mock:
dist    = fedora-14-i386

# whether to refer rpm database:
no_rpmdb   = False

# build rpm with only rpmbuild w/o mock (not recommended):
no_mock    = False
"""


TYPE_FILE    = "file"
TYPE_DIR     = "dir"
TYPE_SYMLINK = "symlink"
TYPE_OTHER   = "other"
TYPE_UNKNOWN = "unknown"


TEST_CHOICES = (TEST_BASIC, TEST_FULL) = ("basic", "full")


STEP_SETUP = "setup"
STEP_PRECONFIGURE = "preconfigure"
STEP_CONFIGURE = "configure"
STEP_SBUILD = "sbuild"
STEP_BUILD = "build"

BUILD_STEPS = (
    # step_name, log_msg_fmt, help_txt
    (STEP_SETUP, "Setting up src tree in %(workdir)s: %(pname)s",
        "setup the package' src dir and copy target files in it"),

    (STEP_PRECONFIGURE, "Making up autotool-ized src directory: %(pname)s",
        "arrange build aux files such like configure.ac, Makefile.am, rpm spec" + \
        "file, debian/* and so on. python-cheetah will be needed."),

    (STEP_CONFIGURE, "Configuring src distribution: %(pname)s",
        "setup src dir to run './configure'. autotools will be needed"),

    (STEP_SBUILD, "Building src package: %(pname)s", "build src package[s]"),

    (STEP_BUILD, "Building bin packages: %(pname)s", "build binary package[s]"),
)



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


@memoize
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


@memoize
def hostname():
    return socket.gethostname() or os.uname()[1]


def date(rfc2822=False, simple=False):
    """TODO: how to output in rfc2822 format w/o email.Utils.formatdate?
    ("%z" for strftime does not look working.)
    """
    if rfc2822:
        fmt = "%a, %d %b %Y %T +0000"
    else:
        fmt = (simple and "%Y%m%d" or "%a %b %_d %Y")

    return datetime.datetime.now().strftime(fmt)


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


@memoize
def get_arch():
    """Returns "normalized" architecutre this host can support.
    """
    ia32_re = re.compile(r"i.86") # i386, i686, etc.

    arch = platform.machine() or "i386"

    if ia32_re.match(arch) is not None:
        return "i386"
    else:
        return arch


@memoize
def is_git_available():
    return os.system("git --version > /dev/null 2> /dev/null") == 0


@memoize
def get_username():
    return os.environ.get("USER", False) or os.getlogin()


@memoize
def get_email():
    if is_git_available():
        try:
            email = subprocess.check_output("git config --get user.email 2>/dev/null", shell=True)
            return email.rstrip()
        except Exception, e:
            logging.warn("get_email: " + str(e))
            pass

    return os.environ.get("MAIL_ADDRESS", False) or "%s@localhost.localdomain" % get_username()


@memoize
def get_fullname():
    """Get full name of the user.
    """
    if is_git_available():
        try:
            fullname = subprocess.check_output("git config --get user.name 2>/dev/null", shell=True)
            return fullname.rstrip()
        except Exception, e:
            logging.warn("get_fullname: " + str(e))
            pass

    return os.environ.get("FULLNAME", False) or get_username()


def get_compressor(compressors=COMPRESSORS):
    global UPTO, CHEETAH_ENABLED

    found = False

    am_dir_pattern = "/usr/share/automake-*"
    am_files_pattern = am_dir_pattern + "/am/*.am"
    
    if len(glob.glob(am_dir_pattern)) == 0:
        UPTO = CHEETAH_ENABLED and STEP_PRECONFIGURE or STEP_SETUP
        logging.warn("Automake looks not installed. Packaging process can go up to \"%s\" step." % UPTO)

        return ("gzip",  "gz",  "")  # fallback to the default.

    for cmd, ext, am_opt in compressors:
        # bzip2 tries compressing input from stdin even it
        # is invoked with --version option. So give null input to it.
        cmd_c = "%s --version > /dev/null 2> /dev/null < /dev/null" % cmd

        if os.system(cmd_c) == 0:
            am_support_c = "grep -q -e '^dist-%s:' %s 2> /dev/null" % (cmd, am_files_pattern)

            if os.system(am_support_c) == 0:
                found = True
                break

    if not found:
        #logging.warn("any compressors not found. Packaging process can go up to \"setup\" step.")
        #UPTO = STEP_SETUP
        #return False

        # gzip must exist at least and not reached here:
        raise RuntimeError("No compressor found! Aborting...")

    return (cmd, ext, am_opt)


def shell(cmd, workdir=None, dryrun=False, stop_on_error=True):
    """
    @cmd      str   command string, e.g. "ls -l ~".
    @workdir  str   in which dir to run given command?
    @dryrun   bool  if True, just print command string to run and returns.
    @stop_on_error bool  if True, RuntimeError will not be raised.

    >>> assert 0 == shell("echo ok > /dev/null")
    >>> assert 0 == shell("ls null", "/dev")
    >>> assert 0 == shell("ls null", "/dev", dryrun=True)
    >>> try:
    ...    rc = shell("ls", "/root")
    ... except RuntimeError:
    ...    pass
    >>> rc = shell("echo OK | grep -q NG 2>/dev/null", stop_on_error=False)
    """
    logging.info(" Run: %s [%s]" % (cmd, workdir))

    if dryrun:
        logging.info(" exit as we're in dry run mode.")
        return 0

    llevel = logging.getLogger().level
    if llevel < logging.WARN:
        cmd += " > /dev/null"
    elif llevel < logging.INFO:
        cmd += " 2> /dev/null"
    else:
        pass

    try:
        proc = subprocess.Popen(cmd, shell=True, cwd=workdir)
        proc.wait()
        rc = proc.returncode

    except Exception, e:
        raise RuntimeError("Error (%s) when running: %s" % (repr(e.__class__), str(e)))

    if rc == 0:
        return rc
    else:
        if stop_on_error:
            raise RuntimeError(" Failed: %s,\n rc=%d" % (cmd, rc))
        else:
            logging.error(" cmd=%s, rc=%d" % (cmd, rc))
            return rc


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


class TestDecoratedFuncs(unittest.TestCase):
    """It seems that doctests in decorated functions become out of scope and
    not executed during running doctests. This class is a workaround for this
    issue.
    """

    _multiprocess_can_split_ = True

    def test_memoize(self):
        fun_0 = lambda a: a * 2
        memoized_fun_0 = memoize(fun_0)

        self.assertEquals(fun_0(2), memoized_fun_0(2))
        self.assertEquals(memoized_fun_0(3), memoized_fun_0(3))

    def test_checksum_null(self):
        """if checksum() returns null
        """
        self.assertEquals(checksum(), "0" * len(sha1("").hexdigest()))

    def test_is_foldable(self):
        """if is_foldable() works as expected.
        """
        self.assertTrue(is_foldable([]))
        self.assertTrue(is_foldable(()))
        self.assertTrue(is_foldable(x for x in range(3)))
        self.assertFalse(is_foldable(None))
        self.assertFalse(is_foldable(True))
        self.assertFalse(is_foldable(1))

    def test_flatten(self):
        """if flatten() works as expected.
        """
        self.assertListEqual(flatten([]), [])
        self.assertListEqual(flatten([[1, 2, 3], [4, 5]]), [1, 2, 3, 4, 5])
        self.assertListEqual(flatten([[1, 2, [3]], [4, [5, 6]]]), [1, 2, 3, 4, 5, 6])
        self.assertListEqual(flatten([(1, 2, 3), (4, 5)]), [1, 2, 3, 4, 5])
        self.assertListEqual(flatten((i, i * 2) for i in range(5)), [0, 0, 1, 2, 2, 4, 3, 6, 4, 8])

    def test_concat(self):
        """if concat() works as expected.
        """
        self.assertListEqual(concat([[]]), [])
        self.assertListEqual(concat((())), [])
        self.assertListEqual(concat([[1, 2, 3], [4, 5]]), [1, 2, 3, 4, 5])
        self.assertListEqual(concat([[1, 2, [3]], [4, [5, 6]]]), [1, 2, [3], 4, [5, 6]])
        self.assertListEqual(concat([(1, 2, [3]), (4, [5, 6])]), [1, 2, [3], 4, [5, 6]])
        self.assertListEqual(concat((i, i * 2) for i in range(5)), [0, 0, 1, 2, 2, 4, 3, 6, 4, 8])

    def test_unique(self):
        """if unique() works as expected.
        """
        self.assertListEqual(unique([]), [])
        self.assertListEqual(unique([0, 3, 1, 2, 1, 0, 4, 5]), [0, 1, 2, 3, 4, 5])

    def test_hostname(self):
        self.assertEquals(hostname(), subprocess.check_output("hostname").rstrip())

    def test_get_username(self):
        self.assertEquals(get_username(), subprocess.check_output("id -un", shell=True).rstrip())



class TestFuncsWithSideEffects(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test_createdir_normal(self):
        """TODO: Check mode (permission).
        """
        d = os.path.join(self.workdir, "a")
        createdir(d)

        self.assertTrue(os.path.isdir(d))

    def test_createdir_specials(self):
        # assertIsNone is not available in python < 2.5:
        #self.assertIsNone(createdir(self.workdir))
        self.assertEquals(createdir(self.workdir), None)  # try creating dir already exists.

        f = os.path.join(self.workdir, "a")
        open(f, "w").write("test")
        self.assertRaises(RuntimeError, createdir, f)

    def test_get_compressor(self):
        _ = (_cmd, _ext, _am_opt) = get_compressor()

    def test_shell(self):
        rc = shell("echo \"\" > /dev/null", os.curdir)
        self.assertEquals(rc, 0)

        self.assertRaises(RuntimeError, shell, "grep xyz /dev/null")

        if os.getuid() != 0:
            self.assertRaises(RuntimeError, shell, "ls", "/root")

    def test_init_defaults_by_conffile_config(self):
        conf = """\
[DEFAULT]
a: aaa
b: bbb
"""
        path = os.path.join(self.workdir, "config")
        open(path, "w").write(conf)

        params = init_defaults_by_conffile(path)
        assert params["a"] == "aaa"
        assert params["b"] == "bbb"

    def test_init_defaults_by_conffile_config_and_profile_0(self):
        conf = """\
[profile0]
a: aaa
b: bbb
"""
        path = os.path.join(self.workdir, "config_p0")
        open(path, "w").write(conf)

        params = init_defaults_by_conffile(path, "profile0")
        assert params["a"] == "aaa"
        assert params["b"] == "bbb"



class Rpm(object):

    RPM_FILELIST_CACHE = os.path.join(os.environ["HOME"], ".cache", "pmaker.rpm.filelist.pkl")

    # RpmFi (FileInfo) keys:
    fi_keys = ("path", "size", "mode", "mtime", "flags", "rdev", "inode",
        "nlink", "state", "vflags", "uid", "gid", "checksum")

    @staticmethod
    def ts(rpmdb_path=None):
        if rpmdb_path is not None:
            rpm.addMacro("_dbpath", rpmdb_path)

        return rpm.TransactionSet()

    @staticmethod
    def pathinfo(path):
        """Get meta data of file or dir from RPM Database.

        @path    Path of the file or directory (relative or absolute)
        @return  A dict; keys are fi_keys (see below)
        """
        _path = os.path.abspath(path)

        try:
            fis = [h.fiFromHeader() for h in Rpm.ts().dbMatch("basenames", _path)]
            if fis:
                xs = [x for x in fis[0] if x and x[0] == _path]
                if xs:
                    return dict(zip(Rpm.fi_keys, xs[0]))
        except:  # FIXME: Careful excpetion handling
            pass

        return dict()

    @staticmethod
    def each_fileinfo_by_package(pname="", pred=true):
        """RpmFi (File Info) of installed package, matched packages or all
        packages generator.

        @pname  str       A package name or name pattern (ex. "kernel*") or ""
                          which means all packages.
        @pred   function  A predicate to sort out only necessary results.
                          $pred :: RpmFi -> bool.

        @return  A dict which has keys (Rpm.fi_keys and "package" = package name)
                 and corresponding values.

        @see rpm/python/rpmfi-py.c
        """
        if "*" in pname:
            mi = Rpm.ts().dbMatch()
            mi.pattern("name", rpm.RPMMIRE_GLOB, pname)

        elif pname:
            mi = Rpm.ts().dbMatch("name", pname)

        else:
            mi = Rpm.ts().dbMatch()

        for h in mi:
            for fi in h.fiFromHeader():
                if pred(fi):
                    yield dict(zip(Rpm.fi_keys + ["package",], list(fi) + [h["name"],]))

        # Release them to avoid core dumped or getting wrong result next time.
        del mi

    @memoized
    def filelist(self, cache=True, expires=1, pkl_proto=pickle.HIGHEST_PROTOCOL, rpmdb_path=None):
        """TODO: It should be a heavy and time-consuming task. How to shorten
        this time? - caching, utilize yum's file list database or whatever.
        """
        data = None

        cache_file = self.RPM_FILELIST_CACHE
        cachedir = os.path.dirname(cache_file)

        if not os.path.exists(cachedir):
            os.makedirs(cachedir, 0755)

        if cache and not cache_needs_updates_p(cache_file, expires):
            try:
                data = pickle.load(open(cache_file, "rb"))
                logging.debug(" Could load the cache: %s" % cache_file)
            except:
                logging.warn(" Could not load the cache: %s" % cache_file)
                date = None

        if data is None:
            data = dict(concat(((f, rpmh2nvrae(h)) for f in h["filenames"]) for h in Rpm.ts(rpmdb_path).dbMatch()))

            try:
                # TODO: How to detect errors during/after pickle.dump.
                pickle.dump(data, open(cache_file, "wb"), pkl_proto)
                logging.debug(" Could save the cache: %s" % cache_file)
            except:
                logging.warn(" Could not save the cache: %s" % cache_file)

        return data



if YUM_ENABLED:
    rpmdb = rpmsack.RPMDBPackageSack()

    @memoize
    def rpm_search_provides_by_path(path):
        rs = rpmdb.searchProvides(path)
        return rs and rpmh2nvrae(rs[0]) or {}
else:
    @memoize
    def rpm_search_provides_by_path(path):
        database = Rpm().filelist(rpmdb_path)
        return database.get(path, {})



class TestRpm(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.do_test = os.path.exists("/var/lib/rpm/Basenames")

    def test_pathinfo(self):
        if not self.do_test:
            return

        f1 = "/etc/fstab"
        pm = "/proc/mounts"

        if os.path.exists(f1):
            pi = Rpm.pathinfo(f1)
            assert pi.get("path") == f1
            assert sorted(pi.keys()) == sorted(Rpm.fi_keys)

        if os.path.exists(pm):
            pi = Rpm.pathinfo(pm)
            assert pi == {}, "result was '%s'" % str(pi)

    def test_filelist(self):
        if not self.do_test:
            return

        f = "/etc/fstab"
        db = Rpm().filelist()
        assert db.get(f)
        assert db.get(f).get("name") == "setup"



class FileOperations(object):
    """Class to implement operations for FileInfo classes.

    This class will not be instatiated and mixed in FileInfo classes.
    """

    @classmethod
    def equals(cls, lhs, rhs):
        """lhs and rhs are identical, that is, these contents and metadata
        (except for path) are exactly same.

        TODO: Compare the part of the path?
          ex. lhs.path: "/path/to/xyz", rhs.path: "/var/lib/sp2/updates/path/to/xyz"

        >>> lhs = FileInfoFactory().create("/etc/resolv.conf")
        >>> rhs = copy.copy(lhs)
        >>> setattr(rhs, "other_attr", "xyz")
        >>> 
        >>> FileOperations.equals(lhs, rhs)
        True
        >>> rhs.mode = "755"
        >>> FileOperations.equals(lhs, rhs)
        False
        """
        keys = ("mode", "uid", "gid", "checksum", "filetype")
        res = all(getattr(lhs, k) == getattr(rhs, k) for k in keys)

        return res and dicts_comp(lhs.xattrs, rhs.xattrs) or False

    @classmethod
    def equivalent(cls, lhs, rhs):
        """These metadata (path, uid, gid, etc.) do not match but the checksums
        are same, that is, that contents are exactly same.

        @lhs  FileInfo object
        @rhs  Likewise

        >>> class FakeFileInfo(object):
        ...     checksum = checksum()
        >>> 
        >>> lhs = FakeFileInfo(); rhs = FakeFileInfo()
        >>> FileOperations.equivalent(lhs, rhs)
        True
        >>> rhs.checksum = checksum("/etc/resolv.conf")
        >>> FileOperations.equivalent(lhs, rhs)
        False
        """
        return lhs.checksum == rhs.checksum

    @classmethod
    def permission(cls, mode):
        """permission (mode) can be passed to "chmod".

        NOTE: There are some special cases, e.g. /etc/gshadow- and
        /etc/shadow-, such that mode == 0.

        @mode  stat.mode

        >>> file0 = "/etc/resolv.conf"
        >>> if os.path.exists(file0):
        ...     mode = os.lstat(file0).st_mode
        ...     expected = oct(stat.S_IMODE(mode & 0777))
        ...     assert expected == FileOperations.permission(mode)
        >>> 
        >>> gshadow = "/etc/gshadow-"
        >>> if os.path.exists(gshadow):
        ...     mode = os.lstat(gshadow).st_mode
        ...     assert "0000" == FileOperations.permission(mode)
        """
        m = stat.S_IMODE(mode & 0777)
        return m == 0 and "0000" or oct(m)

    @classmethod
    def copy_main(cls, fileinfo, dest, use_pyxattr=PYXATTR_ENABLED):
        """Two steps needed to keep the content and metadata of the original file:

        1. Copy itself and its some metadata (owner, mode, etc.)
        2. Copy extra metadata not copyable with the above.

        "cp -a" (cp in GNU coreutils) does the above operations at once and
        might be suited for most cases, I think.

        @fileinfo   FileInfo object
        @dest  str  Destination path to copy to
        @use_pyxattr bool  Whether to use pyxattr module
        """
        if use_pyxattr:
            shutil.copy2(fileinfo.path, dest)  # correponding to "cp -p ..."
            cls.copy_xattrs(fileinfo.xattrs, dest)
        else:
            shell("cp -a %s %s" % (fileinfo.path, dest))

    @classmethod
    def copy_xattrs(cls, src_xattrs, dest):
        """
        @src_xattrs  dict  Xattributes of source FileInfo object to copy
        @dest        str   Destination path
        """
        for k, v in src_xattrs.iteritems():
            xattr.set(dest, k, v)

    @classmethod
    def remove(cls, path):
        os.remove(path)

    @classmethod
    def copy(cls, fileinfo, dest, force=False):
        """Copy to $dest.  "Copy" action varys depends on actual filetype so
        that inherited class must overrride this and related methods (_remove
        and _copy).

        @fileinfo  FileInfo  FileInfo object
        @dest      string    The destination path to copy to
        @force     bool      When True, force overwrite $dest even if it exists
        """
        assert fileinfo.path != dest, "Copying src and dst are same!"

        if not fileinfo.copyable():
            logging.warn(" Not copyable: %s" % str(fileinfo))
            return False

        if os.path.exists(dest):
            logging.warn(" Copying destination already exists: '%s'" % dest)

            # TODO: It has negative impact for symlinks.
            #
            #if os.path.realpath(self.path) == os.path.realpath(dest):
            #    logging.warn("Copying src and dest are same actually.")
            #    return False

            if force:
                logging.info(" Removing old one before copying: " + dest)
                fileinfo.operations.remove(dest)
            else:
                logging.warn(" Do not overwrite it")
                return False
        else:
            destdir = os.path.dirname(dest)

            # TODO: which is better?
            #os.makedirs(os.path.dirname(dest)) or ...
            #shutil.copytree(os.path.dirname(self.path), os.path.dirname(dest))

            if not os.path.exists(destdir):
                os.makedirs(destdir)
            shutil.copystat(os.path.dirname(fileinfo.path), destdir)

        logging.debug(" Copying from '%s' to '%s'" % (fileinfo.path, dest))
        cls.copy_main(fileinfo, dest)

        return True



class DirOperations(FileOperations):

    @classmethod
    def remove(cls, path):
        if not os.path.isdir(path):
            raise RuntimeError(" '%s' is not a directory! Aborting..." % path)

        os.removedirs(path)

    @classmethod
    def copy_main(cls, fileinfo, dest, use_pyxattr=False):
        try:
            mode = int(fileinfo.permission(), 8)  # in octal, e.g. 0755
            os.makedirs(dest, mode)

        except OSError, e:   # It may be OK, ex. non-root user cannot set perms.
            logging.debug("Failed: os.makedirs, dest=%s, mode=%o" % (dest, mode))
            logging.warn(e)

            logging.info("skip to copy " + dest)

            # FIXME: What can be done with it?
            #
            #if not os.path.exists(dest):
            #    os.chmod(dest, os.lstat(dest).st_mode | os.W_OK | os.X_OK)
            #    os.makedirs(dest, mode)

        uid = os.getuid()
        gid = os.getgid()

        if uid == 0 or (uid == fileinfo.uid and gid == fileinfo.gid):
            os.chown(dest, fileinfo.uid, fileinfo.gid)
        else:
            logging.debug("Chown is not permitted so do not")

        shutil.copystat(fileinfo.path, dest)
        cls.copy_xattrs(fileinfo.xattrs, dest)



class SymlinkOperations(FileOperations):

    link_instead_of_copy = False

    @classmethod
    def copy_main(cls, fileinfo, dest, use_pyxattr=False):
        if cls.link_instead_of_copy:
            os.symlink(fileinfo.linkto, dest)
        else:
            shell("cp -a %s %s" % (fileinfo.path, dest))



class TestFileOperations(unittest.TestCase):

    _multiprocess_can_split_ = True

    fo = FileOperations
    nsamples = 10

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.factory = FileInfoFactory()

        paths = glob.glob(os.path.join(os.path.expanduser("~"), ".*"))
        self.paths = random.sample(
            [p for p in paths if os.path.isfile(p)],
            self.nsamples
        )

    def tearDown(self):
        rm_rf(self.workdir)

    def test_copy_main_and_remove(self):
        for path in self.paths:
            fileinfo = self.factory.create(path)

            if fileinfo.type() != TYPE_FILE:
                continue

            dest = os.path.join(self.workdir, os.path.basename(path))
            dest2 = dest + ".xattrs"

            self.fo.copy_main(fileinfo, dest)
            self.fo.copy_main(fileinfo, dest2, True)

            src_attrs = xattr.get_all(path)
            if src_attrs:
                self.assertEquals(src_attrs, xattr.get_all(dest))
                self.assertEquals(src_attrs, xattr.get_all(dest2))

            self.assertTrue(os.path.exists(dest))
            self.assertTrue(os.path.exists(dest2))

            self.fo.remove(dest)
            self.assertFalse(os.path.exists(dest))

            self.fo.remove(dest2)
            self.assertFalse(os.path.exists(dest2))

    def test_copy(self):
        for path in self.paths:
            fileinfo = self.factory.create(path)

            if fileinfo.type() != TYPE_FILE:
                continue

            dest = os.path.join(self.workdir, os.path.basename(path))

            self.fo.copy(fileinfo, dest)
            self.fo.copy(fileinfo, dest, True)

            self.assertTrue(os.path.exists(dest))
            self.fo.remove(dest)
            self.assertFalse(os.path.exists(dest))



class TestDirOperations(unittest.TestCase):

    _multiprocess_can_split_ = True

    fo = DirOperations
    nsamples = 10

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.factory = FileInfoFactory()

        paths = glob.glob(os.path.join(os.path.expanduser("~"), ".*")) + \
            glob.glob(os.path.join("/etc/skel/", ".*"))
        self.paths = random.sample(
            [p for p in paths if os.path.isdir(p) and not os.path.islink(p)],
            self.nsamples
        )

    def tearDown(self):
        rm_rf(self.workdir)

    def test_copy(self):
        for path in self.paths:
            fileinfo = self.factory.create(path)

            if fileinfo.type() != TYPE_DIR:
                continue

            dest = os.path.join(self.workdir, os.path.basename(path))

            self.fo.copy(fileinfo, dest)
            self.fo.copy(fileinfo, dest, True)

            self.assertTrue(os.path.exists(dest))
            self.fo.remove(dest)
            self.assertFalse(os.path.exists(dest))



class TestSymlinkOperations(unittest.TestCase):

    _multiprocess_can_split_ = True

    fo = SymlinkOperations
    nsamples = 3

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.factory = FileInfoFactory()

        paths = glob.glob(os.path.join(os.path.expanduser("~"), ".*"))
        self.paths = random.sample(paths, self.nsamples)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_copy(self):
        for path in self.paths:
            shell("ln -s %s ./" % path, self.workdir)
            path = os.path.join(self.workdir, os.path.basename(path))
            dest = path + ".symlnk"

            fileinfo = self.factory.create(path)

            if fileinfo.type() != TYPE_SYMLINK:
                continue

            self.fo.copy(fileinfo, dest)
            self.fo.copy(fileinfo, dest, True)

            self.assertTrue(os.path.exists(dest))
            self.fo.remove(dest)
            self.assertFalse(os.path.exists(dest))



class FileInfo(object):
    """The class of which objects to hold meta data of regular files, dirs and
    symlinks. This is for regular file and the super class for other types.
    """

    operations = FileOperations
    filetype = TYPE_FILE
    is_copyable = True

    def __init__(self, path, mode, uid, gid, checksum, xattrs, **kwargs):
        self.path = path
        self.realpath = os.path.realpath(path)

        self.mode = mode
        self.uid= uid
        self.gid = gid
        self.checksum = checksum
        self.xattrs = xattrs or {}

        self.perm_default = "0644"

        self.rpmattr = None

        self.target = path

        for k, v in kwargs.iteritems():
            self[k] = v

    @classmethod
    def type(cls):
        return cls.filetype

    @classmethod
    def copyable(cls):
        return cls.is_copyable

    @classmethod
    def register(cls, fmaps=FILEINFOS):
        fmaps[cls.type()] = cls

    def __eq__(self, other):
        return self.operations(self, other)

    def equivalent(self, other):
        return self.operations.equivalent(self, other)

    def permission(self):
        return self.operations.permission(self.mode)

    def need_to_chmod(self):
        return self.permission() != self.perm_default

    def need_to_chown(self):
        return self.uid != 0 or self.gid != 0  # 0 == root

    def copy(self, dest, force=False):
        return self.operations.copy(self, dest, force)

    def rpm_attr(self):
        if self.rpmattr is None:
            if self.need_to_chmod() or self.need_to_chown():
                return rpm_attr(self) + " "
            else:
                return ""
        else:
            return self.rpmattr + " "



class DirInfo(FileInfo):

    operations = DirOperations
    filetype = TYPE_DIR

    def __init__(self, path, mode, uid, gid, checksum, xattrs):
        super(DirInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)
        self.perm_default = "0755"

    def rpm_attr(self):
        return super(DirInfo, self).rpm_attr() + "%dir "



class SymlinkInfo(FileInfo):

    operations = SymlinkOperations
    filetype = TYPE_SYMLINK

    def __init__(self, path, mode, uid, gid, checksum, xattrs):
        super(SymlinkInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)
        self.linkto = os.path.realpath(path)

    def need_to_chmod(self):
        return False



class OtherInfo(FileInfo):
    """$path may be a socket, FIFO (named pipe), Character Dev or Block Dev, etc.
    """
    filetype = TYPE_OTHER
    is_copyable = False

    def __init__(self, path, mode, uid, gid, checksum, xattrs):
        super(OtherInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)



class UnknownInfo(FileInfo):
    """Special case that lstat() failed and cannot stat $path.
    """
    filetype = TYPE_UNKNOWN
    is_copyable = False

    def __init__(self, path, mode=-1, uid=-1, gid=-1, checksum=checksum(), xattrs={}):
        super(UnknownInfo, self).__init__(path, mode, uid, gid, checksum, xattrs)



FileInfo.register()
DirInfo.register()
SymlinkInfo.register()
OtherInfo.register()
UnknownInfo.register()


class FileInfoFactory(object):

    def _stat(self, path):
        """
        @path    str     Object's path (relative or absolute)
        @return  A tuple of (mode, uid, gid) or (None, None, None) if OSError was raised.
        """
        try:
            _stat = os.lstat(path)
        except OSError, e:
            logging.warn(e)
            return (None, None, None)

        return (_stat.st_mode, _stat.st_uid, _stat.st_gid)

    def _guess_ftype(self, st_mode):
        """
        @st_mode    st_mode
        """
        if stat.S_ISLNK(st_mode):
            ft = TYPE_SYMLINK

        elif stat.S_ISREG(st_mode):
            ft = TYPE_FILE

        elif stat.S_ISDIR(st_mode):
            ft = TYPE_DIR

        elif stat.S_ISCHR(st_mode) or stat.S_ISBLK(st_mode) \
            or stat.S_ISFIFO(st_mode) or stat.S_ISSOCK(st_mode):
            ft = TYPE_OTHER
        else:
            ft = TYPE_UNKNOWN  # Should not be reached

        return ft

    def create(self, path, attrs=None, fileinfo_maps=FILEINFOS):
        """Factory method. Create and return the *Info instance.

        @path   str   Object path (relative or absolute)
        @attrs  dict  Attributes set to FileInfo object result after creation
        """
        st = self._stat(path)

        if st is None:
            return UnknownInfo(path)

        (_mode, _uid, _gid) = st

        xs = xattr.get_all(path)
        _xattrs = (xs and dict(xs) or {})

        _filetype = self._guess_ftype(_mode)

        if _filetype == TYPE_UNKNOWN:
            logging.info(" Could not get the result: %s" % path)

        if _filetype == TYPE_FILE:
            _checksum = checksum(path)
        else:
            _checksum = checksum()

        _cls = fileinfo_maps.get(_filetype, False)
        assert _cls, "Should not reached here! filetype=%s" % _filetype

        fi = _cls(path, _mode, _uid, _gid, _checksum, _xattrs)

        if attrs:
            for attr, val in attrs.iteritems():
                setattr(fi, attr, val)

        return fi



class TestFileInfoFactory(unittest.TestCase):

    _multiprocess_can_split_ = True

    def helper_path_check(self, filepath):
        if os.path.exists(filepath):
            return True
        else:
            logging.info("File %s does not look exists. skip this test." % filepath)
            return False

    def helper_guess_ftype(self, filepath, expected_type):
        def st_mode(f):
            return os.lstat(f)[0]

        if os.path.exists(filepath):
            self.assertEquals(expected_type, FileInfoFactory()._guess_ftype(st_mode(filepath)))
        else:
            logging.info("File %s does not look exists. skip this test." % filepath)
            return False

    def test__stat(self):
        f = "/etc/hosts"

        if not self.helper_path_check(f):
            return

        (_mode, uid, gid) = FileInfoFactory()._stat(f)

        self.assertEquals(uid, 0)
        self.assertEquals(gid, 0)

    def test__stat_user_file(self):
        for f in (os.path.expanduser("~/" + p) for p in (".bashrc", ".zshrc", ".tcshrc")):
            if os.path.exists(f):
                break

        if not self.helper_path_check(f):
            return

        (_mode, uid, gid) = FileInfoFactory()._stat(f)

        self.assertEquals(uid, os.getuid())
        self.assertEquals(gid, os.getgid())

    def test__stat_might_fail(self):
        if os.getuid() == 0:
            logging.info("The testing user is root. skip this test.")
            return

        f = "/root/.bashrc"

        (mode, uid, gid) = FileInfoFactory()._stat(f)

        self.assertEquals(mode, None)
        self.assertEquals(uid, None)
        self.assertEquals(gid, None)

    def test__guess_ftype(self):
        data = (
            ("/etc/grub.conf", TYPE_SYMLINK),
            ("/etc/hosts", TYPE_FILE),
            ("/etc", TYPE_DIR),
            ("/dev/null", TYPE_OTHER)
        )

        for f, et in data:
            self.helper_guess_ftype(f, et)

    def test_create(self):
        global FILEINFOS

        data = (
            ("/etc/grub.conf", TYPE_SYMLINK),
            ("/etc/hosts", TYPE_FILE),
            ("/etc", TYPE_DIR),
            ("/dev/null", TYPE_OTHER)
        )

        ff = FileInfoFactory()

        for f, et in data:
            self.assertTrue(isinstance(ff.create(f), FILEINFOS.get(et)))



class RpmFileInfoFactory(FileInfoFactory):

    def _stat(self, path):
        """Stat with using RPM database instead of lstat().

        There are cases to get no results if the target objects not owned by
        any packages.
        """
        try:
            fi = Rpm.pathinfo(path)
            if fi:
                uid = pwd.getpwnam(fi["uid"]).pw_uid   # uid: name -> id
                gid = grp.getgrnam(fi["gid"]).gr_gid   # gid: name -> id

                return (fi["mode"], uid, gid)
        except:
            pass

        return super(RpmFileInfoFactory, self)._stat(path)



class TestRpmFileInfoFactory(unittest.TestCase):

    _multiprocess_can_split_ = True

    def helper_00(self, filepath):
        if not os.path.exists("/var/lib/rpm/Basenames"):
            logging.info("rpmdb does not look exists. skip this test.")
            return False

        if not os.path.exists(filepath):
            logging.info("File %s does not look exists. skip this test." % filepath)
            return False

        return True

    def test__stat(self):
        f = "/etc/hosts"

        if not self.helper_00(f):
            return

        (_mode, uid, gid) = RpmFileInfoFactory()._stat(f)

        self.assertEquals(uid, 0)
        self.assertEquals(gid, 0)

    def test__stat_call_parent_method(self):
        for f in (os.path.expanduser("~/" + p) for p in (".bashrc", ".zshrc", ".tcshrc")):
            if os.path.exists(f):
                break

        if not self.helper_00(f):
            return

        (_mode, uid, gid) = RpmFileInfoFactory()._stat(f)

        self.assertEquals(uid, os.getuid())
        self.assertEquals(gid, os.getgid())



def distdata_in_makefile_am(paths, srcdir="src"):
    """
    @paths  file path list

    >>> ps0 = ["/etc/resolv.conf", "/etc/sysconfig/iptables"]
    >>> rs0 = [{"dir": "/etc", "files": ["src/etc/resolv.conf"], "id": "0"}, {"dir": "/etc/sysconfig", "files": ["src/etc/sysconfig/iptables"], "id": "1"}]
    >>> 
    >>> ps1 = ps0 + ["/etc/sysconfig/ip6tables", "/etc/modprobe.d/dist.conf"]
    >>> rs1 = [{"dir": "/etc", "files": ["src/etc/resolv.conf"], "id": "0"}, {"dir": "/etc/sysconfig", "files": ["src/etc/sysconfig/iptables", "src/etc/sysconfig/ip6tables"], "id": "1"}, {"dir": "/etc/modprobe.d", "files": ["src/etc/modprobe.d/dist.conf"], "id": "2"}]
    >>> 
    >>> _cmp = lambda ds1, ds2: all([dicts_comp(*dt) for dt in zip(ds1, ds2)])
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


def rpm_attr(fileinfo):
    """Returns "%attr(...)" to specify the file/dir attribute, will be used in
    the %files section in rpm spec.

    >>> fi = FileInfo("/dummy/path", 33204, 0, 0, checksum(),{})
    >>> assert rpm_attr(fi) == "%attr(0664, -, -)"
    >>> fi = FileInfo("/bin/foo", 33261, 1, 1, checksum(),{})
    >>> assert rpm_attr(fi) == "%attr(0755, bin, bin)"
    """
    m = fileinfo.permission() # ex. "0755"
    u = (fileinfo.uid == 0 and "-" or pwd.getpwuid(fileinfo.uid).pw_name)
    g = (fileinfo.gid == 0 and "-" or grp.getgrgid(fileinfo.gid).gr_name)

    return "%%attr(%(m)s, %(u)s, %(g)s)" % {"m":m, "u":u, "g":g,}


def rpmh2nvrae(h):
    """
    @h  Rpm header-like object to allow access such like $header["name"].
    """
    return dict((k, h[k]) for k in ("name", "version", "release", "arch", "epoch"))


def srcrpm_name_by_rpmspec(rpmspec):
    """Returns the name of src.rpm gotten from given RPM spec file.
    """
    cmd = "rpm -q --specfile --qf \"%{n}-%{v}-%{r}.src.rpm\n\" " + rpmspec
    out = subprocess.check_output(cmd, shell=True)
    return out.split("\n")[0]


def srcrpm_name_by_rpmspec_2(rpmspec):
    """Returns the name of src.rpm gotten from given RPM spec file.

    Utilize rpm python binding instead of calling "rpm" command.

    FIXME: rpm-python does not look stable and dumps core often.
    """
    p = rpm.TransactionSet().parseSpec(rpmspec).packages[0]
    h = p.header
    return "%s-%s-%s.src.rpm" % (h["n"], h["v"], h["r"])


def do_nothing(*args, **kwargs):
    return


def on_debug_mode():
    return logging.getLogger().level < logging.INFO



class TestMiscFunctions(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test_rpm_attr(self):
        """
        TODO: tests for dirs and symlinks.
        """
        f0 = os.path.join(self.workdir, "afile")
        f1 = os.path.join(self.workdir, "adir")
        f2 = os.path.join(self.workdir, "asymlink")
        gshadow = "/etc/gshadow-"

        def run_or_die(cmd, errmsg=None):
            if 0 != os.system(cmd):
                em = errmsg is None and "Could not run: " + cmd or errmsg
                raise RuntimeError(em)

        run_or_die("touch " + f0)
        run_or_die("mkdir -p " + f1)
        run_or_die("cd %s && ln -s %s %s" % (self.workdir, f0, f2))

        ff = FileInfoFactory()

        user = pwd.getpwuid(os.getuid()).pw_name
        group = grp.getgrgid(os.getgid()).gr_name

        fi = ff.create(f0)
        run_or_die("chmod %s %s" % (fi.perm_default, f0))
        self.assertEquals(rpm_attr(fi), "%%attr(%s, %s, %s)" % (fi.perm_default, user, group))

        for m in ("0755", "0664"):  # TODO: "chmod 1755 ..." does not look worked.
            run_or_die("chmod %s %s" % (m, f0))
            self.assertEquals(rpm_attr(ff.create(f0)), "%%attr(%s, %s, %s)" % (m, user, group))



class Target(object):

    def __init__(self, path, attrs={}):
        self.path = path
        self.attrs = []

        for attr, val in attrs.iteritems():
            if attr == "path":
                continue

            setattr(self, attr, val)
            self.attrs.append(attr)

    def __cmp__(self, other):
        return cmp(self.path, other.path)

    def attrs(self):
        return self.attrs

    def path(self):
        return path



class FileInfoFilter(object):
    """
    Base class to filter out specific FileInfo objects and make them not
    collected when Collector.collect() runs.
    """

    def __init__(self, *args, **kwargs):
        pass

    def pred(self, fileinfo):
        """
        Predicate to filter out fileinfos of which type is not file, symlink or
        dir.  (filter out rule).

        @fileinfo  FileInfo object

        >>> factory = FileInfoFactory()
        >>> ff = FileInfoFilter()
        >>> def test_ifexists(path, expected=True):
        ...     if os.path.exists(path):
        ...         assert expected == ff.pred(factory.create(path))
        ...     else:
        ...         logging.warn("%s does not exist. Skip this test" % path)
        >>> test_ifexists("/etc/resolv.conf", False)  # file
        >>> test_ifexists("/etc/rc", False)  # symlink
        >>> test_ifexists("/etc", False)  # dir
        >>> test_ifexists("/dev/null", True)  # dev
        >>> paths = glob.glob("/tmp/orbit-%s/*" % get_username())
        >>> if paths:
        ...     test_ifexists(paths[0], True)  # socket
        """
        assert isinstance(fileinfo, FileInfo)

        if fileinfo.type() in (TYPE_FILE, TYPE_SYMLINK, TYPE_DIR):
            return False
        else:
            logging.warn("Not supported type and filtered out: '%s' (type=%s)" % (fileinfo.path, fileinfo.type()))
            return True



class FileInfoModifier(object):
    """
    Base class to transform some specific attributes of FileInfo objects during
    Collector.collect().
    """

    _priority = 0

    def __init__(self, *args, **kwargs):
        pass

    def __cmp__(self, other):
        return cmp(self._priority, other._priority)

    def update(self, fileinfo, *args, **kwargs):
        """Just returns given fileinfo w/ no modification.

        @fileinfo FileInfo object
        @target   Target objecr
        """
        return fileinfo



class DestdirModifier(FileInfoModifier):

    _priority = 1

    def __init__(self, destdir):
        self.destdir = destdir

    def rewrite_with_destdir(self, path):
        """Rewrite target (install destination) path by assuming path is
        consist of DESTDIR and actual installation path and stripping DESTDIR.

        >>> assert DestdirModifier("/a/b").rewrite_with_destdir("/a/b/c") == "/c"
        >>> assert DestdirModifier("/a/b/").rewrite_with_destdir("/a/b/c") == "/c"
        >>> try:
        ...     DestdirModifier("/x/y").rewrite_with_destdir("/a/b/c")
        ... except RuntimeError, e:
        ...     pass
        """
        if path.startswith(self.destdir):
            new_path = path.split(self.destdir)[1]
            if not new_path.startswith(os.path.sep):
                new_path = os.path.sep + new_path

            logging.debug("Rewrote target path from %s to %s" % (path, new_path))
            return new_path
        else:
            logging.error(" The path '%s' does not start with '%s'" % (path, self.destdir))
            raise RuntimeError("Destdir and the actual file path are inconsistent.")

    def update(self, fileinfo, *args, **kwargs):
        fileinfo.target = self.rewrite_with_destdir(fileinfo.path)
        return fileinfo



class OwnerModifier(FileInfoModifier):

    _priority = 5

    def __init__(self, owner_uid=0, owner_gid=0):
        self.uid = owner_uid
        self.gid = owner_gid

    def update(self, fileinfo, *args, **kwargs):
        fileinfo.uid = self.uid
        fileinfo.gid = self.gid

        return fileinfo


class RpmConflictsModifier(FileInfoModifier):

    _priority = 6

    def __init__(self, package, rpmdb_path=None):
        """
        @package  str  Name of the package to be built
        """
        self.package = package

        self.savedir = CONFLICTS_SAVEDIR % {"name": package}
        self.newdir = CONFLICTS_NEWDIR % {"name": package}

    def find_owner(self, path):
        """Find the package owns given path.

        @path  str  File/dir/symlink path
        """
        owner_nvrae = rpm_search_provides_by_path(path)

        if owner_nvrae and owner_nvrae["name"] != self.package:
            logging.warn("%s is owned by %s" % (path, owner_nvrae["name"]))
            return owner_nvrae
        else:
            return {}

    def update(self, fileinfo, *args, **kwargs):
        fileinfo.conflicts = self.find_owner(fileinfo.target)

        if fileinfo.conflicts:
            fileinfo.original_path = fileinfo.target

            path = fileinfo.target[1:]  # strip "/" at the head.
            fileinfo.target = os.path.join(self.newdir, path)
            fileinfo.save_path = os.path.join(self.savedir, path)

        return fileinfo



class TargetAttributeModifier(FileInfoModifier):

    _priority = 9

    def __init__(self, overrides=()):
        """
        @overrides  attribute names to override.
        """
        self.overrides = overrides

    def update(self, fileinfo, target, *args, **kwargs):
        """
        @fileinfo  FileInfo object
        @target    Target object
        """
        attrs_to_override = self.overrides and self.overrides or target.attrs

        for attr in attrs_to_override:
            if attr == "path":  # fileinfo.path must not be overridden.
                logging.warn("You cannot overwrite original path of the fileinfo: path=" + fileinfo.path)
                continue

            val = getattr(target, attr, None)
            if val is not None:
                logging.info("Override attr %s=%s in fileinfo: path=%s" % (attr, val, fileinfo.path))
                setattr(fileinfo, attr, val)

        return fileinfo



class TestDestdirModifier(unittest.TestCase):

    _multiprocess_can_split_ = True

    target_path = "/etc/resolv.conf"

    def setUp(self):
        destdir = "/destdir"
        mode = "0644"
        csum = checksum(self.target_path)

        self.fileinfos = [
            FileInfo(destdir + self.target_path, mode, 0, 0, csum, {}),
            FileInfo("/not_destdir" + self.target_path, mode, 0, 0, csum, {}),
        ]

        self.modifier = DestdirModifier(destdir)

    def test_update_ok(self):
        new_fileinfo = self.modifier.update(self.fileinfos[0])

        self.assertEquals(new_fileinfo.target, self.target_path)

    def test_update_ng(self):
        self.assertRaises(RuntimeError, self.modifier.update, self.fileinfos[1])



class TestOwnerModifier(unittest.TestCase):

    _multiprocess_can_split_ = True

    target_path = "/etc/resolv.conf"

    def setUp(self):
        mode = "0644"
        csum = checksum(self.target_path)
        self.owner = (uid, gid) = (500, 500)

        self.fileinfos = [
            FileInfo(self.target_path, mode, uid, gid, csum, {}),
        ]

        self.modifier = OwnerModifier(0, 0)

    def test_update(self):
        new_fileinfo = self.modifier.update(self.fileinfos[0])

        self.assertEquals(new_fileinfo.uid, 0)
        self.assertEquals(new_fileinfo.gid, 0)



class TestTargetAttributeModifier(unittest.TestCase):

    _multiprocess_shared_ = True

    target_path = "/etc/resolv.conf"

    def setUp(self):
        mode = "0644"
        csum = checksum(self.target_path)
        self.owner = (uid, gid) = (500, 500)

        self.fileinfo = FileInfo(self.target_path, mode, uid, gid, csum, {})
        self.target = Target(
            self.target_path,
            {
                "target": "/var/lib/network/resolv.conf",
                "uid": 0,
                "gid": 0,
                "mode": "0600",
                "rpmattr": "%config"
            }
        )

    def test_update(self):
        tgt = copy.copy(self.target)

        modifier = TargetAttributeModifier()
        new_fileinfo = modifier.update(self.fileinfo, tgt)

        for attr in tgt.attrs:
            self.assertEquals(getattr(new_fileinfo, attr, None), getattr(tgt, attr, None))

    def test__init__with_overrides(self):
        tgt = copy.copy(self.target)
        tgt.target = os.path.join(self.target_path + ".d", os.path.basename(self.target_path))

        modifier = TargetAttributeModifier(("target", ))
        new_fileinfo = modifier.update(self.fileinfo, tgt)

        self.assertEquals(new_fileinfo.target, tgt.target)



class Collector(object):
    """Abstract class for collector classes
    """

    _enabled = True
    _type = None

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def type(cls):
        return cls._type

    @classmethod
    def register(cls, cmaps=COLLECTORS):
        if cls.enabled():
            cmaps[cls.type()] = cls

    @classmethod
    def enabled(cls):
        return cls._enabled

    def make_enabled(self):
        self._enabled = True

    def collect(self, *args, **kwargs):
        if not self.enabled():
            raise RuntimeError("Pluing %s cannot run as necessary function is not available." % self.__name__)

    def get_modifiers(self):
        """
        Returns registered modifiers sorted by these priorities.
        """
        for m in sorted(self.modifiers):
            yield m



class FilelistCollector(Collector):
    """
    Collector to collect fileinfo list from files list in simple format:

    Format: A file or dir path (absolute or relative) |
            Comment line starts with "#" |
            Glob pattern to list multiple files or dirs
    """

    _type = "filelist"

    def __init__(self, filelist, pkgname, options):
        """
        @filelist  str  file to list files and dirs to collect or "-"
                        (read files and dirs list from stdin)
        @pkgname   str  package name to build
        @options   optparse.Values
        """
        super(FilelistCollector, self).__init__(filelist, options)

        self.filelist = filelist

        # TBD:
        #self.trace = options.trace
        self.trace = False

        self.filters = [FileInfoFilter()]
        self.modifiers = []

        if options.destdir:
            self.modifiers.append(DestdirModifier(options.destdir))

        if options.ignore_owner:
            self.modifiers.append(OwnerModifier(0, 0))  # 0 == root's uid and gid

        if options.format == "rpm":
            self.fi_factory = RpmFileInfoFactory()

            if not options.no_rpmdb:
                self.modifiers.append(RpmConflictsModifier(pkgname))
        else:
            self.fi_factory = FileInfoFactory()

    @staticmethod
    def open(path):
        return path == "-" and sys.stdin or open(path)

    @classmethod
    def _parse(cls, line):
        """Parse the line and returns Target (path) list.
        """
        if not line or line.startswith("#"):
            return []
        else:
            return [Target(p) for p in glob.glob(line.rstrip())]

    def list_targets(self, listfile):
        """Read paths from given file line by line and returns path list sorted by
        dir names. There some speical parsing rules for the file list:

        * Empty lines or lines start with "#" are ignored.
        * The lines contain "*" (glob match) will be expanded to real dir or file
          names: ex. "/etc/httpd/conf/*" will be
          ["/etc/httpd/conf/httpd.conf", "/etc/httpd/conf/magic", ...] .

        @listfile  str  Path list file name or "-" (read list from stdin)
        """
        return unique(concat(self._parse(l) for l in self.open(listfile).readlines()))

    def _collect(self, listfile):
        """Collect FileInfo objects from given path list.

        @listfile  str  File, dir and symlink paths list
        """
        fileinfos = []

        for target in self.list_targets(listfile):
            fi = self.fi_factory.create(target.path)
            fi.conflicts = {}
            fi.target = fi.path

            # Too verbose but useful in some cases:
            if self.trace:
                logging.debug(" fi=%s" % str(fi))

            for filter in self.filters:
                if filter.pred(fi):  # filter out if pred -> True:
                    continue

            for modifier in self.get_modifiers():
                fi = modifier.update(fi, target, self.trace)

            fileinfos.append(fi)

        return fileinfos

    def collect(self):
        return self._collect(self.filelist)



class ExtFilelistCollector(FilelistCollector):
    """
    Collector to collect fileinfo list from files list in simple format:

    Format: A file or dir path (absolute or relative) |
            Comment line starts with "#" |
            Glob pattern to list multiple files or dirs
    """
    _enabled = True
    _type = "filelist.ext"

    def __init__(self, filelist, pkgname, options):
        super(ExtFilelistCollector, self).__init__(filelist, pkgname, options)
        self.modifiers.append(TargetAttributeModifier())

    @staticmethod
    def parse_line(line):
        """
        >>> cls = ExtFilelistCollector
        >>> cls.parse_line("/etc/resolv.conf,target=/var/lib/network/resolv.conf,uid=0,gid=0\\n")
        ('/etc/resolv.conf', [('target', '/var/lib/network/resolv.conf'), ('uid', 0), ('gid', 0)])
        """
        path_attrs = line.rstrip().split(",")
        path = path_attrs[0]
        attrs = []

        for attr, val in (kv.split("=") for kv in path_attrs[1:]):
            attrs.append((attr, parse_conf_value(val)))   # e.g. "uid=0" -> ("uid", 0), etc.

        return (path, attrs)

    @classmethod
    def _parse(cls, line):
        """Parse the line and returns Target (path) list.

        TODO: support glob expression in path.

        >>> cls = ExtFilelistCollector
        >>> cls._parse("#\\n")
        []
        >>> cls._parse("")
        []
        >>> cls._parse(" ")
        []
        >>> t = Target("/etc/resolv.conf", {"target": "/var/lib/network/resolv.conf", "uid": 0, "gid": 0})
        >>> ts = cls._parse("/etc/resolv.conf,target=/var/lib/network/resolv.conf,uid=0,gid=0\\n")
        >>> assert [t] == ts, str(ts)
        """
        if not line or line.startswith("#") or " " in line:
            return []
        else:
            (path, attrs) = cls.parse_line(line)
            return [Target(path, dict(attrs)) for path, attrs in zip(glob.glob(path), [attrs])]



class JsonFilelistCollector(FilelistCollector):
    """
    Collector for files list in JSON format such as:

    [
        {
            "path": "/a/b/c",
            "target": {
                "target": "/a/c",
                "uid": 100,
                "gid": 0,
                "rpmattr": "%config(noreplace)",
                ...
            }
        },
        ...
    ]
    """
    global JSON_ENABLED

    _enabled = JSON_ENABLED
    _type = "filelist.json"

    def __init__(self, filelist, pkgname, options):
        super(JsonFilelistCollector, self).__init__(filelist, pkgname, options)
        self.modifiers.append(TargetAttributeModifier())

    @classmethod
    def _parse(cls, path_dict):
        path = path_dict.get("path", False)

        if not path or path.startswith("#"):
            return []
        else:
            return [Target(p, path_dict["target"]) for p in glob.glob(path)]

    def list_targets(self, listfile):
        return unique(concat(self._parse(d) for d in json.load(self.open(listfile))))



FilelistCollector.register()
ExtFilelistCollector.register()
JsonFilelistCollector.register()



class TestFilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test__parse(self):
        p0 = ""
        p1 = "#xxxxx"
        p2 = os.path.join(self.workdir, "a")
        p3 = os.path.join(self.workdir, "aa")
        p4 = os.path.join(self.workdir, "a*")

        for p in (p2, p3):
            os.system("touch " + p)

        ps2 = [Target(p) for p in [p2]]
        ps3 = [Target(p) for p in [p2, p3]]

        self.assertListEqual(FilelistCollector._parse(p0 + "\n"), [])
        self.assertListEqual(FilelistCollector._parse(p1 + "\n"), [])
        self.assertListEqual(FilelistCollector._parse(p2 + "\n"), ps2)
        self.assertListEqual(sorted(FilelistCollector._parse(p4 + "\n")), sorted(ps3))

    def test_list_targets(self):
        paths = [
            "/etc/auto.*",
            "#/etc/aliases.db",
            "/etc/httpd/conf.d",
            "/etc/httpd/conf.d/*",
            "/etc/modprobe.d/*",
            "/etc/rc.d/init.d",
            "/etc/rc.d/rc",
            "/etc/reslv.conf",
        ]
        listfile = os.path.join(self.workdir, "files.list")

        f = open(listfile, "w")
        f.write("\n")
        for p in paths:
            f.write("%s\n" % p)
        f.close()

        option_values = {
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, "foo", options)

        ts = unique(concat(FilelistCollector._parse(p + "\n") for p in paths))
        self.assertListEqual(ts, fc.list_targets(listfile))

    def test_collect(self):
        paths = [
            "/etc/auto.*",
            "#/etc/aliases.db",
            "/etc/httpd/conf.d",
            "/etc/httpd/conf.d/*",
            "/etc/modprobe.d/*",
            "/etc/rc.d/init.d",
            "/etc/rc.d/rc",
            "/etc/resolv.conf",
            "/etc/reslv.conf",  # should not be exist.
        ]
        listfile = os.path.join(self.workdir, "files.list")

        f = open(listfile, "w")
        for p in paths:
            f.write("%s\n" % p)
        f.close()

        option_values = {
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, "foo", options)
        fs = fc.collect()

        option_values["format"] = "deb"
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, "foo", options)
        fs = fc.collect()
        option_values["format"] = "rpm"

        option_values["destdir"] = "/etc"
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, "foo", options)
        fs = fc.collect()
        option_values["destdir"] = ""

        option_values["ignore_owner"] = True
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, "foo", options)
        fs = fc.collect()
        option_values["ignore_owner"] = False

        option_values["no_rpmdb"] = True
        options = optparse.Values(option_values)
        fc = FilelistCollector(listfile, "foo", options)
        fs = fc.collect()
        option_values["no_rpmdb"] = False



class TestExtFilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

    def tearDown(self):
        rm_rf(self.workdir)

    def test_collect(self):
        paths = [
            "/etc/auto.*,uid=0,gid=0",
            "#/etc/aliases.db",
            "/etc/rc.d/rc,target=/etc/init.d/rc,uid=0,gid=0",
            "/etc/rc.d/rc.local,rpmattr=%config(noreplace)",
        ]
        listfile = os.path.join(self.workdir, "files.list")

        f = open(listfile, "w")
        for p in paths:
            f.write("%s\n" % p)
        f.close()

        option_values = {
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = ExtFilelistCollector(listfile, "foo", options)
        fs = fc.collect()



class TestJsonFilelistCollector(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        self.json_data = """\
[
    {
        "path": "/etc/resolv.conf",
        "target": {
            "target": "/var/lib/network/resolv.conf",
            "uid": 0,
            "gid": 0,
            "conflicts": "NetworkManager"
        }
    },
    {
        "path": "/etc/hosts",
        "target": {
            "conflicts": "setup",
            "rpmattr": "%config(noreplace)"
        }
    }
]
"""

    def tearDown(self):
        rm_rf(self.workdir)

    def test_list_targets(self):
        listfile = os.path.join(self.workdir, "files.json")

        f = open(listfile, "w")
        f.write(self.json_data)
        f.close()

        option_values = {
            "format": "rpm",
            "destdir": "",
            "ignore_owner": False,
            "no_rpmdb": False,
        }

        options = optparse.Values(option_values)
        fc = ExtFilelistCollector(listfile, "foo", options)

        ts = fc.list_targets(listfile)
        #self.assertListEqual(ts, ts2)



def to_srcdir(srcdir, path):
    """
    >>> srcdir = "/tmp/w/src"
    >>> assert to_srcdir(srcdir, "/a/b/c") == "/tmp/w/src/a/b/c"
    >>> assert to_srcdir(srcdir, "a/b") == "/tmp/w/src/a/b"
    >>> assert to_srcdir(srcdir, "/") == "/tmp/w/src/"
    """
    assert path != "", "Empty path was given"

    return os.path.join(srcdir, path.strip(os.path.sep))



class PackageMaker(object):
    """Abstract class for classes to implement various packaging processes.
    """
    global BUILD_STEPS, TEMPLATES, COLLECTORS

    _templates = TEMPLATES
    _type = "filelist"
    _format = None
    _collector = FilelistCollector
    _relations = {}

    _collector_maps = COLLECTORS

    _steps = BUILD_STEPS

    @classmethod
    def register(cls, pmmaps=PACKAGE_MAKERS):
        pmmaps[(cls.type(), cls.format())] = cls

    @classmethod
    def templates(cls):
        return cls._templates

    @classmethod
    def type(cls):
        return cls._type

    @classmethod
    def format(cls):
        return cls._format

    def collector(self):
        return self._collector

    def __init__(self, package, filelist, options, *args, **kwargs):
        self.package = package
        self.filelist = filelist
        self.options = options

        self.workdir = package["workdir"]
        self.destdir = package["destdir"]
        self.pname = package["name"]

        self.force = options.force
        self.upto = options.upto

        self.srcdir = os.path.join(self.workdir, "src")

        self._collector = self._collector_maps.get(options.itype, FilelistCollector)
        logging.info("Use Collector: %s (%s)" % (self._collector.__name__, options.itype))

        relmap = []
        if package.has_key("relations"):
            for reltype, reltargets in package["relations"]:
                rel = self._relations.get(reltype, False)
                if rel:
                    relmap.append({"type": rel, "targets": reltargets})

        self.package["relations"] = relmap

        self.package["conflicts_savedir"] = CONFLICTS_SAVEDIR % self.package
        self.package["conflicts_newdir"] = CONFLICTS_NEWDIR % self.package

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def shell(self, cmd_s):
        return shell(cmd_s, workdir=self.workdir)

    def to_srcdir(self, path):
        return to_srcdir(self.srcdir, path)

    def genfile(self, path, output=False):
        outfile = os.path.join(self.workdir, (output or path))
        open(outfile, "w").write(compile_template(self.templates()[path], self.package))

    def copyfiles(self):
        for fi in self.package["fileinfos"]:
            fi.copy(os.path.join(self.workdir, self.to_srcdir(fi.target)), self.force)

    def dumpfile_path(self):
        return os.path.join(self.workdir, "pmaker-package-filelist.pkl")

    def save(self, pkl_proto=pickle.HIGHEST_PROTOCOL):
        pickle.dump(self.package["fileinfos"], open(self.dumpfile_path(), "wb"), pkl_proto)

    def load(self):
        self.package["fileinfos"] = pickle.load(open(self.dumpfile_path()))

    def touch_file(self, step):
        return os.path.join(self.workdir, "pmaker-%s.stamp" % step)

    def try_the_step(self, step):
        if os.path.exists(self.touch_file(step)):
            msg = "...The step looks already done"

            if self.force:
                logging.info(msg + ": " + step)
            else:
                logging.info(msg + ". Skip the step: " + step)
                return

        getattr(self, step, do_nothing)() # TODO: or eval("self." + step)() ?
        self.shell("touch %s" % self.touch_file(step))

        if step == self.upto:
            if step == STEP_BUILD:
                logging.info("Successfully created packages in %s: %s" % (self.workdir, self.pname))
            sys.exit()

    def collect(self, *args, **kwargs):
        collector = self.collector()(self.filelist, self.package["name"], self.options)
        return collector.collect()

    def setup(self):
        self.package["fileinfos"] = self.collect()

        for d in ("workdir", "srcdir"):
            createdir(self.package[d])

        self.copyfiles()
        self.save()

    def preconfigure(self):
        if not self.package.get("fileinfos", False):
            self.load()

        self.package["distdata"] = distdata_in_makefile_am(
            [fi.target for fi in self.package["fileinfos"] if fi.type() == TYPE_FILE]
        )

        self.package["conflicted_fileinfos"] = [fi for fi in self.package["fileinfos"] if fi.conflicts]
        self.package["not_conflicted_fileinfos"] = [fi for fi in self.package["fileinfos"] if not fi.conflicts]

        _dirname = lambda fi: os.path.dirname(fi.original_path)
        self.package["conflicted_fileinfos_groupby_dir"] = \
            [(dir, list(fis_g)) for dir, fis_g in groupby(self.package["conflicted_fileinfos"], _dirname)]

        self.genfile("configure.ac")
        self.genfile("Makefile.am")
        self.genfile("README")
        self.genfile("MANIFEST")
        self.genfile("MANIFEST.overrides")
        self.genfile("apply-overrides")
        self.genfile("revert-overrides")

    def configure(self):
        if on_debug_mode():
            self.shell("autoreconf -vfi")
        else:
            self.shell("autoreconf -fi")

    def sbuild(self):
        if on_debug_mode():
            self.shell("./configure --quiet")
            self.shell("make")
            self.shell("make dist")
        else:
            self.shell("./configure --quiet --enable-silent-rules")
            self.shell("make V=0 > /dev/null")
            self.shell("make dist V=0 > /dev/null")

    def build(self):
        pass

    def run(self):
        """run all of the packaging processes: setup, configure, build, ...
        """
        d = {"workdir": self.workdir, "pname": self.pname}

        for step, msgfmt, _helptxt in self._steps:
            logging.info(msgfmt % d)
            self.try_the_step(step)



class TgzPackageMaker(PackageMaker):
    _format = "tgz"



class RpmPackageMaker(TgzPackageMaker):
    _format = "rpm"

    _relations = {
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

    def rpmspec(self):
        return os.path.join(self.workdir, "%s.spec" % self.pname)

    def build_srpm(self):
        if on_debug_mode:
            return self.shell("make srpm")
        else:
            return self.shell("make srpm V=0 > /dev/null")

    def build_rpm(self):
        use_mock = not self.options.no_mock

        if use_mock:
            try:
                self.shell("mock --version > /dev/null")
            except RuntimeError, e:
                logging.warn(" It seems mock is not found on your system. Fallback to plain rpmbuild...")
                use_mock = False

        if use_mock:
            silent = (on_debug_mode() and "" or "--quiet")
            self.shell("mock -r %s %s %s" % \
                (self.package["dist"], srcrpm_name_by_rpmspec(self.rpmspec()), silent)
            )
            print "  GEN    rpm"  # mimics the message of "make rpm"
            return self.shell("mv /var/lib/mock/%(dist)s/result/*.rpm %(workdir)s" % self.package)
        else:
            if on_debug_mode:
                return self.shell("make rpm")
            else:
                return self.shell("make rpm V=0 > /dev/null")

    def preconfigure(self):
        super(RpmPackageMaker, self).preconfigure()

        self.genfile("rpm.mk")
        self.genfile("package.spec", "%s.spec" % self.pname)

    def sbuild(self):
        super(RpmPackageMaker, self).sbuild()

        self.build_srpm()

    def build(self):
        super(RpmPackageMaker, self).build()

        self.build_rpm()



class DebPackageMaker(TgzPackageMaker):
    _format = "deb"

    # TODO: Add almost relation tag set:
    _relations = {
        "requires": "Depends",
    }

    def preconfigure(self):
        super(DebPackageMaker, self).preconfigure()

        debiandir = os.path.join(self.workdir, "debian")

        if not os.path.exists(debiandir):
            os.makedirs(debiandir, 0755)

        os.makedirs(os.path.join(debiandir, "source"), 0755)

        self.genfile("debian/rules")
        self.genfile("debian/control")
        self.genfile("debian/copyright")
        self.genfile("debian/changelog")
        self.genfile("debian/dirs")
        self.genfile("debian/compat")
        self.genfile("debian/source/format")
        self.genfile("debian/source/options")

        os.chmod(os.path.join(self.workdir, "debian/rules"), 0755)

    def sbuild(self):
        """FIXME: What should be done for building source packages?
        """
        super(DebPackageMaker, self).sbuild()
        self.shell("dpkg-buildpackage -S")

    def build(self):
        """Which is better to build?

        * debuild -us -uc
        * fakeroot debian/rules binary
        """
        super(DebPackageMaker, self).build()
        self.shell("fakeroot debian/rules binary")



TgzPackageMaker.register()
RpmPackageMaker.register()
DebPackageMaker.register()



def load_plugins(package_makers_map=PACKAGE_MAKERS):
    plugins = os.path.join(get_python_lib(), "pmaker", "*plugin*.py")
    csfx = "PackageMaker"

    for modpy in glob.glob(plugins):
        modn = os.path.basename(modpy).replace(".py")
        mod = __import__("pmaker.%s" % modn)
        pms = [c for n, c in inspect.getmembers(mod) if inspect.isclass(c) and n.endswith(csfx)]
        c.register(package_makers_map)


def do_packaging(pkg, filelist, options, pmaps=PACKAGE_MAKERS):
    cls = pmaps.get((options.type, options.format), TgzPackageMaker)
    logging.info("Use PackageMaker: %s: type=%s, format=%s" % (cls.__name__, cls.type(), cls.format()))
    cls(pkg, filelist, options).run()


def do_packaging_self(options):
    if options.pversion:
        version = options.pversion
    else:
        version = __version__

        if not options.release_build:
            version += ".%s" % date(simple=True)

    plugin_files = []
    if options.include_plugins:
        plugin_files = options.include_plugins.split(",")

    name = __title__
    workdir = tempfile.mkdtemp(dir="/tmp", prefix="pm-")
    summary = "A python script to build packages from existing files on your system"
    relations = "requires:python"
    packager = __author__
    mail = __email__
    url = __website__

    pkglibdir = os.path.join(workdir, get_python_lib()[1:], "pmaker")
    bindir = os.path.join(workdir, "usr", "bin")
    bin = os.path.join(bindir, "pmaker")

    filelist = os.path.join(workdir, "files.list")

    prog = sys.argv[0]

    cmd_opts = "-n %s --pversion %s -w %s --license GPLv3+ --ignore-owner " % (name, version, workdir)
    cmd_opts += " --destdir %s --no-rpmdb --url %s --upto %s" % (workdir, url, options.upto)
    cmd_opts += " --summary \"%s\" --packager \"%s\" --mail %s" % (summary, packager, mail)

    if relations:
        cmd_opts += " --relations \"%s\" " % relations

    if options.debug:
        cmd_opts += " --debug"

    if options.no_mock:
        cmd_opts += " --no-mock"

    if options.dist:
        cmd_opts += " --dist %s" % options.dist

    if options.format:
        cmd_opts += " --format %s" % options.format

    createdir(pkglibdir, mode=0755)
    shell("install -m 644 %s %s/__init__.py" % (prog, pkglibdir))

    for f in plugin_files:
        if not os.path.exists(f):
            logging.warn("Plugin %s does not found. Skip it" % f)
            continue

        nf = f.replace("pmaker-", "")
        shell("install -m 644 %s %s" % (f, os.path.join(pkglibdir, nf)))

    createdir(bindir)

    open(bin, "w").write("""\
#! /usr/bin/python
import sys, pmaker

pmaker.main(sys.argv)
""")
    shell("chmod +x %s" % bin)

    open(filelist, "w").write("""\
%s
%s/*
""" % (bin, pkglibdir))

    # @see /usr/lib/rpm/brp-python-bytecompile:
    pycompile = "import compileall, os; compileall.compile_dir(os.curdir, force=1)"
    compile_pyc = "python -c \"%s\"" % pycompile
    compile_pyo = "python -O -c \"%s\" > /dev/null" % pycompile

    shell(compile_pyc, pkglibdir)
    shell(compile_pyo, pkglibdir)

    cmd = "python %s %s %s" % (prog, cmd_opts, filelist)

    logging.info(" executing: %s" % cmd)
    os.system(cmd)


def show_examples(logs=EXAMPLE_LOGS):
    for log in logs:
        print >> sys.stdout, log


def dump_rc(rc=EXAMPLE_RC):
    print >> sys.stdout, rc



class TestMainProgram00SingleFileCases(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        target = "/etc/resolv.conf"
        self.cmd = "echo %s | python %s -n resolvconf -w %s " % (target, sys.argv[0], self.workdir)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_packaging_setup_wo_rpmdb(self):
        """Setup without rpm database
        """
        cmd = self.cmd + "--upto setup --no-rpmdb -"
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_configure_wo_rpmdb(self):
        """Configure without rpm database
        """
        cmd = self.cmd + "--upto configure --no-rpmdb -"
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_sbuild_wo_rpmdb_wo_mock(self):
        """Build src package without rpm database without mock
        """
        cmd = self.cmd + "--upto sbuild --no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.src.rpm" % self.workdir)) > 0)

    def test_packaging_build_rpm_wo_rpmdb_wo_mock(self):
        """Build package without rpm database without mock
        """
        cmd = self.cmd + "--upto build --no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_wo_rpmdb_wo_mock(self):
        """Build package without rpm database without mock (no --upto option)
        """
        cmd = self.cmd + "--no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_with_relations_wo_rpmdb_wo_mock(self):
        """Build package with some additional relations without rpm database
        without mock (no --upto option).
        """
        cmd = self.cmd + "--relations \"requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old\" "
        cmd += "--no-rpmdb --no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

        rpmspec = glob.glob("%s/*/*.spec" % self.workdir)[0]
        cmds = (
            "grep -q -e '^Requires:.*bash, zsh' %s" % rpmspec,
            "grep -q -e '^Obsoletes:.*sysdata' %s" % rpmspec,
            "grep -q -e '^Conflicts:.*sysdata-old' %s" % rpmspec,
        )

        for cmd in cmds:
            self.assertEquals(os.system(cmd), 0)

    def test_packaging_symlink_wo_rpmdb_wo_mock(self):
        idir = os.path.join(self.workdir, "var", "lib", "net")
        os.makedirs(idir)
        os.symlink("/etc/resolv.conf", os.path.join(idir, "resolv.conf"))

        cmd = "echo %s/resolv.conf | python %s -n resolvconf -w %s --no-rpmdb --no-mock -" % (idir, sys.argv[0], self.workdir)

        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_wo_rpmdb_wo_mock_with_destdir(self):
        destdir = os.path.join(self.workdir, "destdir")
        createdir(os.path.join(destdir, "etc"))
        shell("cp /etc/resolv.conf %s/etc" % destdir)

        cmd = "echo %s/etc/resolv.conf | python %s -n resolvconf -w %s --no-rpmdb --no-mock --destdir=%s -" % \
            (destdir, sys.argv[0], self.workdir, destdir)

        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_wo_rpmdb_wo_mock_with_compressor(self):
        (zcmd, _zext, _z_am_opt) = get_compressor()

        if zcmd == "xz":
            zchoices = ["bz2", "gz"]

        elif zcmd == "bzip2":
            zchoices = ["gz"]

        else:
            return  # only "gz" is available and cannot test others.

        for z in zchoices:
            cmd = self.cmd + "--no-rpmdb --no-mock --upto sbuild --compressor %s -" % z

            self.assertEquals(os.system(cmd), 0)

            archives = glob.glob("%s/*/*.tar.%s" % (self.workdir, z))
            self.assertFalse(archives == [], "failed with --compressor " + z)

            if z != zchoices[-1]:
                for x in glob.glob("%s/*" % self.workdir):
                    rm_rf(x)

    def test_packaging_with_rpmdb_wo_mock(self):
        cmd = self.cmd + "--no-mock -"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_with_rpmdb_with_mock(self):
        network_avail = os.system("ping -q -c 1 -w 1 github.com > /dev/null 2> /dev/null") == 0

        if not network_avail:
            logging.warn("Network does not look available right now. Skip this test.")
            return

        cmd = self.cmd + "-"
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)

    def test_packaging_deb(self):
        """'dh' may not be found on this system so that it will only go up to
        "configure" step.
        """
        cmd = self.cmd + "--upto configure --format deb --no-rpmdb -"
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_with_rc(self):
        rc = os.path.join(self.workdir, "rc")
        prog = sys.argv[0]

        #PMAKERRC=./pmakerrc.sample python pmaker.py files.list --upto configure
        cmd = "python %s --dump-rc > %s" % (prog, rc)
        self.assertEquals(os.system(cmd), 0)

        cmd = "echo /etc/resolv.conf | PMAKERRC=%s python %s -w %s --upto configure -" % (rc, prog, self.workdir)
        self.assertEquals(os.system(cmd), 0)

    def test_packaging_wo_rpmdb_wo_mock_with_a_custom_template(self):
        global TEMPLATES

        prog = sys.argv[0]
        tmpl0 = os.path.join(self.workdir, "package.spec")

        open(tmpl0, "w").write(TEMPLATES["package.spec"])

        cmd = self.cmd + "--no-rpmdb --no-mock --templates=\"package.spec:%s\" -" % tmpl0
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.src.rpm" % self.workdir)) > 0)



class TestMainProgram01JsonFileCases(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")
        self.json_data = """\
[
    {
        "path": "/etc/resolv.conf",
        "target": {
            "target": "/var/lib/network/resolv.conf",
            "uid": 0,
            "gid": 0
        }
    }
]
"""
        self.listfile = os.path.join(self.workdir, "filelist.json")
        self.cmd = "python %s -n resolvconf -w %s --itype filelist.json " % (sys.argv[0], self.workdir)

    def tearDown(self):
        rm_rf(self.workdir)

    def test_packaging_with_rpmdb_wo_mock(self):
        f = open(self.listfile, "w")
        f.write(self.json_data)
        f.close()

        cmd = self.cmd + "--no-mock " + self.listfile
        self.assertEquals(os.system(cmd), 0)
        self.assertTrue(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)) > 0)



class TestMainProgram01MultipleFilesCases(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.workdir = tempfile.mkdtemp(dir="/tmp", prefix="pmaker-tests")

        self.filelist = os.path.join(self.workdir, "file.list")

        targets = [
            "/etc/auto.*", "/etc/modprobe.d/*", "/etc/resolv.conf",
            "/etc/security/limits.conf", "/etc/security/access.conf",
            "/etc/grub.conf", "/etc/system-release", "/etc/skel",
        ]
        self.files = [f for f in targets if os.path.exists(f)]

    def tearDown(self):
        rm_rf(self.workdir)

    def test_packaging_build_rpm_wo_mock(self):
        open(self.filelist, "w").write("\n".join(self.files))

        cmd = "python %s -n etcdata -w %s --upto build --no-mock %s" % (sys.argv[0], self.workdir, self.filelist)
        self.assertEquals(os.system(cmd), 0)
        self.assertEquals(len(glob.glob("%s/*/*.src.rpm" % self.workdir)), 1)
        self.assertEquals(len(glob.glob("%s/*/*.noarch.rpm" % self.workdir)), 2) # etcdata and etcdata-overrides



def run_doctests(verbose):
    doctest.testmod(verbose=verbose, raise_on_error=True)


def run_unittests(verbose, test_choice):
    def tsuite(testcase):
        return unittest.TestLoader().loadTestsFromTestCase(testcase)

    basic_tests = [
        TestDecoratedFuncs,
        TestFuncsWithSideEffects,
        TestFileInfoFactory,
        TestRpmFileInfoFactory,
        TestFileOperations,
        TestDirOperations,
        TestSymlinkOperations,
        TestMiscFunctions,
        TestDestdirModifier,
        TestOwnerModifier,
        TestTargetAttributeModifier,
        TestFilelistCollector,
        TestExtFilelistCollector,
        TestJsonFilelistCollector,
    ]

    system_tests = [
        TestRpm,
        TestMainProgram00SingleFileCases,
        TestMainProgram01JsonFileCases,
        TestMainProgram01MultipleFilesCases,
    ]

    (major, minor) = sys.version_info[:2]

    suites = [tsuite(c) for c in basic_tests]

    if test_choice == TEST_FULL:
        suites += [tsuite(c) for c in system_tests]

    tests = unittest.TestSuite(suites)

    if major == 2 and minor < 5:
        unittest.TextTestRunner().run(tests)
    else:
        unittest.TextTestRunner(verbosity=(verbose and 2 or 0)).run(tests)


def run_alltests(verbose, test_choice):
    run_doctests(verbose)
    run_unittests(verbose, test_choice)


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

    def matched(pat, s):
        m = pat.match(s)
        return m is not None

    if not s:
        return ""

    if matched(boolp, s):
        return bool(s)

    if matched(intp, s):
        return int(s)

    if matched(listp, s):
        return eval(s)  # TODO: too danger. safer parsing should be needed.

    return s


def parse_template_list_str(templates):
    """
    simple parser for options.templates.

    >>> assert parse_template_list_str("") == {}
    >>> assert parse_template_list_str("a:b") == {"a": "b"}
    >>> assert parse_template_list_str("a:b,c:d") == {"a": "b", "c": "d"}
    """
    if templates:
        return dict(kv.split(":") for kv in templates.split(","))
    else:
        return dict()


def init_defaults_by_conffile(config=None, profile=None, prog="pmaker"):
    """
    Initialize default values for options by loading config files.
    """
    if config is None:
        home = os.environ.get("HOME", os.curdir) # Is there case that $HOME is empty?

        confs = ["/etc/%s.conf" % prog]
        confs += sorted(glob.glob("/etc/%s.d/*.conf" % prog))
        confs += [os.environ.get("%sRC" % prog.upper(), os.path.join(home, ".%src" % prog))]
    else:
        confs = (config,)

    cparser = cp.SafeConfigParser()
    loaded = False

    for c in confs:
        if os.path.exists(c):
            logging.info("Loading config: %s" % c)
            cparser.read(c)
            loaded = True

    if not loaded:
        return {}

    if profile:
        defaults = dict((k, parse_conf_value(v)) for k,v in cparser.items(profile))
    else:
        defaults = cparser.defaults()

#    for sec in cparser.sections():
#        defaults.update(dict(((k, parse_conf_value(v)) for k, v in cparser.items(sec))))

    return defaults


def option_parser(V=__version__, pmaps=PACKAGE_MAKERS, itypes=COLLECTORS,
        test_choices=TEST_CHOICES, steps=BUILD_STEPS,
        compressors=COMPRESSORS, upto=UPTO):

    ver_s = "%prog " + V

    upto_params = {
        "choices": [name for name, _logmsg, helptxt in steps],
        "choices_str": ", ".join(("%s (%s)" % (name, helptxt) for name, _logmsg, helptxt in steps)),
        "default": upto,
    }

    pdriver = unique([tf[0] for tf in pmaps.keys()])
    pdriver_help = "Package driver type: " + ", ".join(pdriver) + " [%default]"

    pformats = unique([tf[1] for tf in pmaps.keys()])
    pformats_help = "Package format: " + ", ".join(pformats) + " [%default]"

    itypes = sorted(itypes.keys())
    itypes_help = "Input type: " + ", ".join(itypes) + " [%default]"

    mail = get_email()
    packager = get_fullname()
    dist = "fedora-14-%s" % get_arch()

    compressor = get_compressor(compressors)  # cmd, extension, am_option,
    compressor_choices = [ext for _c, ext, _a in compressors]

    workdir = os.path.join(os.path.abspath(os.curdir), "workdir")

    cds = init_defaults_by_conffile()

    defaults = {
        "workdir": cds.get("workdir", workdir),
        "upto": cds.get("upto", upto_params["default"]),
        "type": cds.get("type", "filelist"),
        "format": cds.get("format", "rpm"),
        "itype": cds.get("itype", "filelist"),
        "compressor": cds.get("compressor", compressor[1]),
        "verbose": cds.get("verbose", False),
        "quiet": cds.get("quiet", False),
        "debug": cds.get("debug", False),
        "ignore_owner": cds.get("ignore_owner", False),
        "destdir": cds.get("destdir", ""),
        "link": cds.get("link", False),
        "with_pyxattr": cds.get("with_pyxattr", False),

        "name": cds.get("name", ""),
        "pversion": cds.get("pversion", "0.1"),
        "group": cds.get("group", "System Environment/Base"),
        "license": cds.get("license", "GPLv2+"),
        "url": cds.get("url", "http://localhost.localdomain"),
        "summary": cds.get("summary", ""),
        "arch": cds.get("arch", False),
        "relations": cds.get("relations", ""),
        "packager": cds.get("packager", packager),
        "mail": cds.get("mail", mail),

        "scriptlets": cds.get("scriptlets", ""),
        "changelog": cds.get("changelog", ""),

         # TODO: Detect appropriate distribution (for mock) automatically.
        "dist": cds.get("dist", dist),
        "no_rpmdb": cds.get("no_rpmdb", False),
        "no_mock": cds.get("no_mock", False),

        "force": False,

        # these are not in conf file:
        "show_examples": False,
        "dump_rc": False,
        "tests": False,
        "tlevel": test_choices[0],
        "build_self": False,
        "profile": False,

        "release_build": False,
        "include_plugins": ",".join(glob.glob("pmaker-plugin-*.py")),
    }

    p = optparse.OptionParser("""%prog [OPTION ...] FILE_LIST

Arguments:

  FILE_LIST  a file contains absolute file paths list or "-" (read paths list
             from stdin).

             The lines starting with "#" in the list file are ignored.

             The "*" character in lines will be treated as glob pattern and
             expanded to the real file names list.

Environment Variables:

  PMAKERRC    Configuration file path. see also: `%prog --dump-rc`

Examples:
  %prog -n foo files.list
  cat files.list | %prog -n foo -  # same as above.

  %prog -n foo --pversion 0.2 -l MIT files.list
  %prog -n foo --relations "requires:httpd,/sbin/service;obsoletes:foo-old" files.list

  %prog --tests --debug  # run test suites

  %prog --build-self    # package itself

  see the output of `%prog --show-examples` for more detailed examples.""",
    version=ver_s
    )
    
    p.set_defaults(**defaults)

    bog = optparse.OptionGroup(p, "Build options")
    bog.add_option("-w", "--workdir", help="Working dir to dump outputs [%default]")
    bog.add_option("", "--upto", type="choice", choices=upto_params["choices"],
        help="Which packaging step you want to proceed to: " + upto_params["choices_str"] + " [Default: %default]")
    bog.add_option("", "--driver", type="choice", choices=pdriver, help=pdriver_help)
    bog.add_option("", "--format", type="choice", choices=pformats, help=pformats_help)
    bog.add_option("", "--itype", type="choice", choices=itypes, help=itypes_help)
    bog.add_option("", "--destdir", help="Destdir (prefix) you want to strip from installed path [%default]. "
        "For example, if the target path is \"/builddir/dest/usr/share/data/foo/a.dat\", "
        "and you want to strip \"/builddir/dest\" from the path when packaging \"a.dat\" and "
        "make it installed as \"/usr/share/foo/a.dat\" with the package , you can accomplish "
        "that by this option: \"--destdir=/builddir/destdir\"")
    bog.add_option("", "--templates", help="Use custom template files. "
        "TEMPLATES is a comma separated list of template output and file after the form of "
        "RELATIVE_OUTPUT_PATH_IN_SRCDIR:TEMPLATE_FILE such like \"package.spec:/tmp/foo.spec.tmpl\", "
        "and \"debian/rules:mydebrules.tmpl, Makefile.am:/etc/foo/mymakefileam.tmpl\". "
        "Supported template syntax is Python Cheetah: http://www.cheetahtemplate.org .")
    bog.add_option("", "--link", action="store_true", help="Make symlinks for symlinks instead of copying them")
    bog.add_option("", "--with-pyxattr", action="store_true", help="Get/set xattributes of files with pure python code.")
    p.add_option_group(bog)

    pog = optparse.OptionGroup(p, "Package metadata options")
    pog.add_option("-n", "--name", help="Package name [%default]")
    pog.add_option("", "--group", help="The group of the package [%default]")
    pog.add_option("", "--license", help="The license of the package [%default]")
    pog.add_option("", "--url", help="The url of the package [%default]")
    pog.add_option("", "--summary", help="The summary of the package")
    pog.add_option("-z", "--compressor", type="choice", choices=compressor_choices,
        help="Tool to compress src archives [%default]")
    pog.add_option("", "--arch", action="store_true", help="Make package arch-dependent [false - noarch]")
    pog.add_option("", "--relations",
        help="Semicolon (;) separated list of a pair of relation type and targets "
        "separated with comma, separated with colon (:), "
        "e.g. \"requires:curl,sed;obsoletes:foo-old\". "
        "Expressions of relation types and targets are varied depends on "
        "package format to use")
    pog.add_option("", "--packager", help="Specify packager's name [%default]")
    pog.add_option("", "--mail", help="Specify packager's mail address [%default]")
    pog.add_option("", "--pversion", help="Specify the package version [%default]")
    pog.add_option("", "--ignore-owner", action="store_true", help="Ignore owner and group of files and then treat as root's")
    pog.add_option("", "--changelog", help="Specify text file contains changelog")
    p.add_option_group(pog)

    rog = optparse.OptionGroup(p, "Options for rpm")
    rog.add_option("", "--dist", help="Target distribution (for mock) [%default]")
    rog.add_option("", "--no-rpmdb", action="store_true", help="Do not refer rpm db to get extra information of target files")
    rog.add_option("", "--no-mock", action="store_true", help="Build RPM with only using rpmbuild (not recommended)")
    rog.add_option("", "--scriptlets", help="Specify the file contains rpm scriptlets")
    p.add_option_group(rog)

    sog = optparse.OptionGroup(p, "Self-build options")
    sog.add_option("", "--release-build", action="store_true", help="Make a release build")
    sog.add_option("", "--include-plugins", help="Comma separated list of plugin files to be included in dist.")
    p.add_option_group(sog)

    tog = optparse.OptionGroup(p, "Test options")
    tog.add_option("", "--tests", action="store_true", help="Run tests.")
    tog.add_option("", "--tlevel", type="choice", choices=test_choices,
        help="Select the level of tests to run. Choices are " + ", ".join(test_choices) + " [%default]")
    tog.add_option("", "--profile", action="store_true", help="Enable profiling")
    p.add_option_group(tog)

    p.add_option("", "--force", action="store_true", help="Force going steps even if the steps looks done")
    p.add_option("-v", "--verbose", action="store_true", help="Verbose mode")
    p.add_option("-q", "--quiet", action="store_true", help="Quiet mode")
    p.add_option("-D", "--debug", action="store_true", help="Debug mode")

    p.add_option("", "--build-self", action="store_true", help="Package itself (self-build)")
    p.add_option("", "--show-examples", action="store_true", help="Show examples")
    p.add_option("", "--dump-rc", action="store_true", help="Show conf file example")

    return p


def relations_parser(relations_str):
    """
    >>> relations_parser("requires:bash,zsh;obsoletes:sysdata;conflicts:sysdata-old")
    [('requires', ['bash', 'zsh']), ('obsoletes', ['sysdata']), ('conflicts', ['sysdata-old'])]
    """
    if not relations_str:
        return []

    rels = [rel.split(":") for rel in relations_str.split(";")]
    return [(reltype, reltargets.split(",")) for reltype, reltargets in rels]


def main(argv=sys.argv, compressors=COMPRESSORS, templates=TEMPLATES):
    global TEMPLATES, PYXATTR_ENABLED

    verbose_test = False

    loglevel = logging.INFO
    logdatefmt = "%H:%M:%S" # too much? "%a, %d %b %Y %H:%M:%S"
    logformat = "%(asctime)s [%(levelname)-4s] %(message)s"

    logging.basicConfig(level=loglevel, format=logformat, datefmt=logdatefmt)

    pkg = dict()

    p = option_parser()
    (options, args) = p.parse_args(argv[1:])

    if options.show_examples:
        show_examples()
        sys.exit(0)

    if options.dump_rc:
        dump_rc()
        sys.exit(0)

    if options.verbose:
        logging.getLogger().setLevel(logging.INFO)
        verbose_test = False
    else:
        logging.getLogger().setLevel(logging.WARNING)
        verbose_test = False

    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        verbose_test = True

    if options.build_self:
        if options.tests:
            rc = os.system("python %s --tests --tlevel=full -v" % argv[0])
            if rc != 0:
                sys.exit(rc)

        do_packaging_self(options)
        sys.exit()

    if options.tests:
        if options.profile:
            import cProfile as profile
            # FIXME: how to do? -  python <self> -m cProfile ...
            print >> sys.stderr, \
                "Not implemented yet. run \"python %s -m cProfile --tests ...\" instead" % \
                        (argv[0], options.tlevel)
            sys.exit()
        else:
            run_alltests(verbose_test, options.tlevel)
        sys.exit()

    if len(args) < 1:
        p.print_usage()
        sys.exit(1)

    filelist = args[0]

    pkg["noarch"] = not options.arch

    if options.templates:
        for tgt, tmpl in parse_template_list_str(options.templates).iteritems():
            if templates.has_key(tgt):
                try:
                    tmpl_content = open(tmpl).read()
                except:
                    logging.warn(" Could not open the template: " + tmpl)
                    tmpl_content = templates[tgt]

                templates[tgt] = tmpl_content
            else:
                logging.warn(" target output %s is not defined in template list" % tgt)

    if options.scriptlets:
        try:
            scriptlets = open(options.scriptlets).read()
        except IOError:
            logging.warn(" Could not open %s to read scriptlets" % options.scriptlets)
            scriptlets = ""

        pkg["scriptlets"] = scriptlets

    if not options.name:
        print >> sys.stderr, "You must specify the package name with \"--name\" option"
        sys.exit(-1)

    pkg["name"] = options.name
    pkg["release"] = "1"
    pkg["group"] = options.group
    pkg["license"] = options.license
    pkg["url"] = options.url

    pkg["version"] = options.pversion
    pkg["packager"] = options.packager
    pkg["mail"] = options.mail

    pkg["workdir"] = os.path.abspath(os.path.join(options.workdir, "%(name)s-%(version)s" % pkg))
    pkg["srcdir"] = os.path.join(pkg["workdir"], "src")

    compressor_am_opt = [am_opt for _c, _ext, am_opt in compressors if _ext == options.compressor][0]

    pkg["compressor"] = {
        "ext": options.compressor,
        "am_opt": compressor_am_opt,
    }

    if options.relations:
        pkg["relations"] = relations_parser(options.relations)

    pkg["dist"] = options.dist

    # TODO: Revert locale setting change just after timestamp was gotten.
    locale.setlocale(locale.LC_ALL, "C")
    pkg["date"] = {
        "date": date(rfc2822=True),
        "timestamp": date(),
    }
    pkg["host"] = hostname()

    pkg["format"] = options.format

    if options.link:
        SymlinkOperations.link_instead_of_copy = True

    if options.with_pyxattr:
        if not PYXATTR_ENABLED:
            logging.warn(" pyxattr module is not found so that it will not be used.")
    else:
        PYXATTR_ENABLED = False

    pkg["destdir"] = options.destdir.rstrip(os.path.sep)

    if options.summary:
        pkg["summary"] = options.summary
    else:
        pkg["summary"] = "Custom package of " + options.name

    if options.changelog:
        try:
            changelog = open(options.changelog).read()
        except IOError:
            logging.warn(" Could not open %s to read changelog" % options.changelog)
            changelog = ""

        pkg["changelog"] = changelog
    else:
        pkg["changelog"] = ""

    do_packaging(pkg, filelist, options)


if __name__ == '__main__':
    main()

# vim: set sw=4 ts=4 expandtab:
