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
$fi.rpm_attr$fi.target
#end for


#if $conflicted_fileinfos
%files          overrides
%defattr(-,root,root,-)
%doc MANIFEST.overrides
%dir $conflicts_savedir
%{_libexecdir}/%{name}-overrides/*-overrides
#for $fi in $conflicted_fileinfos
$fi.rpm_attr$fi.target
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
