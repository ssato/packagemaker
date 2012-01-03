%{!?ruby_sitelib: %global ruby_sitelib %(ruby -rrbconfig -e "puts Config::CONFIG['sitelibdir']")}
%{!?ruby_sitearch: %global ruby_sitearch %(ruby -rrbconfig -e "puts Config::CONFIG['sitearchdir']")}

%define         pkgname #{ name.split("ruby-")[-1] }

Name:           #{name}
Version:        #{version}
Release:        1%{?dist}
Summary:        #{summary}
Group:          Development/Languages
License:        #{license}
URL:            #{url}
Source0:        %{pkgname}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
<?py if _context.get("buildarch"):
?>BuildArch:      #{buildarch}
<?py #endif ?>
BuildRequires:  ruby ruby-devel
<?py if _context.get("dependencies"):
?>BuildRequires:  #{dependencies}
<?py #endif ?>
Requires:       ruby(abi) = 1.8
# If this package is mainly a ruby library, it should provide
# whatever people have to require in their ruby scripts to use the library
# For example, if people use this lib with "require 'foo'", it should provide
# ruby(foo)
Provides:       ruby(%{pkgname})

%description


%prep
%setup -q


%build
export CFLAGS="$RPM_OPT_FLAGS"


%install
rm -rf $RPM_BUILD_ROOT

 
%check


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc
# For noarch packages: ruby_sitelib
%{ruby_sitelib}/*
# For arch-specific packages: ruby_sitearch
%{ruby_sitearch}/*


%changelog
