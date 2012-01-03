Name:           #{name}
Version:        #{version}
Release:        1%{?dist}
Summary:        #{ _context.get("summary", "") }
Group:          System Environment/Libraries
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


%package        devel
Summary:        Development files for %{name}
Group:          Development/Libraries
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.


%prep
%setup -q


%build
%configure --disable-static
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
find $RPM_BUILD_ROOT -name '*.la' -exec rm -f {} ';'


%clean
rm -rf $RPM_BUILD_ROOT


%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig


%files
%defattr(-,root,root,-)
%doc
%{_libdir}/*.so.*

%files devel
%defattr(-,root,root,-)
%doc
%{_includedir}/*
%{_libdir}/*.so


%changelog
