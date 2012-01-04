# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

%define         pkgname #{ name.split("python-")[-1] }

Name:           #{name}
Version:        #{version}
Release:        1%{?dist}
Summary:        #{summary}
Group:          Development/Languages
License:        #{license}
URL:            #{url}
Source0:        %{pkgname}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
<?py if _context.get("dependencies"):
?>BuildRequires:  #{dependencies}
<?py #endif ?>
<?py if _context.get("buildarch"):
?>BuildArch:      #{buildarch}
<?py #endif ?>
BuildRequires:  python-devel
#Requires:


%description
#{description}


%prep
%setup -q


%build
<?py
if _context.get("buildarch") == "noarch":
    cflags = 'CFLAGS="$RPM_OPT_FLAGS" '
else:
    cflags = ""
#endif
?>
#{cflags}%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

 
%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc
# For noarch packages: sitelib
%{python_sitelib}/*
# For arch-specific packages: sitearch
%{python_sitearch}/*


%changelog
