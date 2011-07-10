# disable debuginfo
%define debug_package %{nil}

%define domainxml_savedir  $domain.xmlsavedir
%define domainxml_path     ${domain.xmlsavedir}/${domain.name}.xml

Name:           $name
Version:        $version
Release:        1%{?dist}
Summary:        libvirt domain $domain.name
Group:          $group
License:        $license
URL:            $url
Source0:        %{name}-%{version}.tar.${compressor.ext}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
#for $rel in $relations
$rel.type:      $rel.targets
#end for
PreReq:         /usr/bin/virsh
Requires:       /usr/bin/virsh
Requires:       libvirt
Requires:       %{name}-base


%description
Libvirt domain (virtual) hardware data and disk images for ${domain.name}
on $host packaged by $packager at $date.date.


%prep
%setup -q


%build
%configure
make


%install
rm -rf \$RPM_BUILD_ROOT
make install DESTDIR=\$RPM_BUILD_ROOT


%clean
rm -rf \$RPM_BUILD_ROOT


%post
if [ $1 = 1 -o $1 = 2 ]; then    # install or update
    %{_libexecdir}/%{name}/register-domain
fi


%preun          overrides
if [ $1 = 0 ]; then    # uninstall (! update)
    %{_libexecdir}/%{name}/deregister-domain
fi


%files
%defattr(-,root,root,-)
%doc README
#for $fi in $fileinfos
#if $fi.path in $domain.delta_images
$fi.rpm_attr$fi.target
#end if
#end for


%changelog
* $date.timestamp ${packager} <${mail}> - ${version}-${release}
- Initial packaging.
