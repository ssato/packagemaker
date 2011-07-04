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
#if $noarch or not $arch
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
* $date.timestamp ${packager} <${email}> - ${version}-${release}
- Initial packaging.
#end if
