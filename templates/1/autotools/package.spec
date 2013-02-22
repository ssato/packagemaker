<?py if conflicts.files: ?>
%define  savedir  /var/lib/pmaker/preserved
%define  newdir  /var/lib/pmaker/installed
<?py #endif ?>
<?py if trigger: ?>
%define use_trigger 1
<?py else: ?>
%define use_trigger 0
<?py #endif ?>

Name:           #{name}
Version:        #{pversion}
Release:        #{release}%{?dist}
Summary:        #{summary}
Group:          #{group}
License:        #{license}
URL:            #{url}
Source0:        %{name}-%{version}.tar.#{compressor.ext}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
<?py if not arch: ?>
BuildArch:      noarch
<?py #endif ?>
<?py
for f in files:
    if f.type() == "symlink":
?>
#BuildRequires:  #{f.linkto}
<?py    #endif ?>
<?py #endfor ?>
<?py
for rel in relations:
    rel_targets = ", ".join(rel.targets)
?>
#{rel.type}:       #{rel_targets}
<?py #endfor ?>


%description
This package provides some backup data collected on
#{hostname} by #{packager} at #{date.date}.

<?py
reqs = list(set([(f.conflicts.name, f.conflicts.version, f.conflicts.release, f.conflicts.epoch) for f in conflicts.files]))
?>
<?py if conflicts.files: ?>
%package        overrides
Summary:        Some more extra data override files owned by other packages
Group:          #{group}
Requires:       %{name} = %{version}-%{release}

%if 0%{?use_trigger} == 0
<?py   for name, version, release, epoch in reqs: ?>
Requires:       #{name} = #{epoch}:#{version}-#{release}
<?py   #endfor ?>
%endif


%description    overrides
Some more extra data will override and replace other packages'.
<?py #endif ?>


%prep
%setup -q


%build
%configure --quiet --enable-silent-rules
make %{?_smp_mflags} V=0


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

<?py if conflicts.files: ?>
mkdir -p $RPM_BUILD_ROOT#{conflicts.savedir}
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
install -m 755 apply-overrides $RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
install -m 755 revert-overrides $RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
%if 0%{?use_trigger} == 1
install -m 755 trigger-overrides $RPM_BUILD_ROOT%{_libexecdir}/%{name}-overrides
%endif
<?py #endif ?>


%clean
rm -rf \$RPM_BUILD_ROOT

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

<?py if conflicts.files: ?>
%if 0%{?use_trigger} == 1
<?py for name, version, release, epoch in reqs: ?>
%triggerin -- #{name}
%{_libexecdir}/%{name}-overrides/trigger-overrides
<?py #endfor ?>
%endif
<?py #endif ?>

%files
%defattr(-,root,root,-)
%doc README pmaker-config.json
<?py for f in not_conflicts.files: ?>
#{f.rpm_attr}#{f.install_path}
<?py #endfor ?>


<?py if conflicts.files: ?>
%files          overrides
%doc README pmaker-config.json
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
