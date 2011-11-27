%define  savedir  /var/lib/pmaker/preserved
%define  newdir  /var/lib/pmaker/installed


Name:           #{name}
Version:        #{pversion}
Release:        #{release}
Summary:        #{summary}
Group:          #{group}
<?py if not arch: ?>
BuildArch:      noarch
<?py #endif ?>
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source0:        %{name}-%{version}.tar.gz
<?py
for rel in relations:
    rel_targets = ", ".join(rel.targets)
?>
#{rel.type}:       #{rel_targets}
<?py #endfor ?>
License:        #{license}
URL:            #{url}


%description
This package provides some backup data collected on
#{hostname} by #{packager} at #{date.date}.


<?py if conflicts.files: ?>
%package        overrides
Summary:        Some more extra data override files owned by other packages
Group:          #{group}
Requires:       %{name} = %{version}-%{release}
<?py
reqs = list(
    set(
        [(f.conflicts.name,
          f.conflicts.version,
          f.conflicts.release,
          f.conflicts.epoch
         ) for f in conflicts.files
        ]
    )
)

for name, version, release, epoch in reqs: ?>
Requires:       #{name} = #{epoch}:#{version}-#{release}
<?py #endfor ?>


%description    overrides
Some more extra data will override and replace other packages'.
<?py #endif ?>


%prep
tar -xvzf %_topdir/SOURCES/%{name}-%{version}.tar.gz


%install
cd %{name}-%{version}
mkdir %{buildroot}
cp -Rp *  %{buildroot}/

<?py if conflicts.files: ?>
mkdir -p $RPM_BUILD_ROOT#{conflicts.savedir}
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
install -m 755 apply-overrides $RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
install -m 755 revert-overrides $RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
<?py #endif ?>


%clean 
rm -rf %{buildroot}/


<?py if conflicts.files: ?>
%post           overrides
if [ $1 = 1 -o $1 = 2 ]; then    # install or update
    %{_libexecdir}/%{name}-overrides/apply-overrides
fi


%preun          overrides
if [ $1 = 0 ]; then    # uninstall (! update)
    %{_libexecdir}/%{name}-overrides/revert-overrides
fi
<?py #endif ?>


%files
%defattr(-,root,root,-)
%doc README
<?py for f in not_conflicts.files: ?>
#{f.rpm_attr}#{f.install_path}
<?py #endfor ?>


<?py if conflicts.files: ?>
%files          overrides
%defattr(-,root,root,-)
%dir #{conflicts.savedir}
%{_libexecdir}/%{name}-overrides/*-overrides
<?py for f in conflicts.files: ?>
#{f.rpm_attr}#{f.install_path}
<?py #endfor ?>
<?py #endif ?>


%changelog
<?py if _context.get("changelog", False): ?>
#{changelog}
<?py else: ?>
* #{date.timestamp} #{packager} <#{email}> - #{pversion}-#{release}
- Initial packaging.
<?py #endif ?>
