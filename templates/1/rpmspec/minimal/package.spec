Name:           #{name}
Version:        #{ _context.get("version", "") }
Release:        1%{?dist}
Summary:        #{ _context.get("summary", "") }
Group:          #{ _context.get("group", "") }
License:        #{ _context.get("license", "") }
URL:            #{ _context.get("url", "") }
Source0:        #{ _context.get("source0", "") }
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
<?py if _context.get("buildrequires"): ?>
BuildRequires:  #{buildrequires}
<?py #endif ?>
<?py if _context.get("requires"): ?>
Requires:       #{requires}
<?py #endif ?>

%description
#{ _context.get("description", "") }


%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc


%changelog
