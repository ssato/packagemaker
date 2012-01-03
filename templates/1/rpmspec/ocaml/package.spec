<?py libname = name.split("ocaml-")[-1] ?>

%global opt %(test -x %{_bindir}/ocamlopt && echo 1 || echo 0)
%global debug_package %{nil}
%global _use_internal_dependency_generator 0
%global __find_requires /usr/lib/rpm/ocaml-find-requires.sh
%global __find_provides /usr/lib/rpm/ocaml-find-provides.sh
#%define libname %(echo %{name} | sed -e 's/^ocaml-//')
%define libname #{libname}

Name:           #{name}
Version:        #{ _context.get("version", "") }
Release:        1%{?dist}
Summary:        #{ _context.get("summary", "") }
Group:          Development/Libraries
License:        #{ _context.get("license", "") }
URL:            #{ _context.get("url", "") }
Source0:        #{ _context.get("source0", "") }
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  ocaml >= 3.10.0
BuildRequires:  ocaml-findlib-devel
BuildRequires:  ocaml-ocamldoc
BuildRequires:  chrpath

%description
#{ _context.get("description", "") }


%package        devel
Summary:        Development files for %{name}
Group:          Development/Libraries
Requires:       %{name} = %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and signature files for
developing applications that use %{name}.


%prep
%setup -q -n %{libname}-%{version}


%build
# You may need a %%configure step here (or ./configure if it doesn't work).
make byte
%if %opt
make opt
%endif


%install
rm -rf $RPM_BUILD_ROOT
# These rules work if the library uses 'ocamlfind install' to install itself.
export DESTDIR=$RPM_BUILD_ROOT
export OCAMLFIND_DESTDIR=$RPM_BUILD_ROOT%{_libdir}/ocaml
mkdir -p $OCAMLFIND_DESTDIR $OCAMLFIND_DESTDIR/stublibs
make install

strip $OCAMLFIND_DESTDIR/stublibs/dll*.so
chrpath --delete $OCAMLFIND_DESTDIR/stublibs/dll*.so


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc LICENSE
%dir %{_libdir}/ocaml/%{libname}/
%if %opt
%exclude %{_libdir}/ocaml/*/*.a
%exclude %{_libdir}/ocaml/*/*.cmxa
%exclude %{_libdir}/ocaml/*/*.cmx
%endif
%exclude %{_libdir}/ocaml/*/*.mli
%{_libdir}/ocaml/stublibs/*.so
%{_libdir}/ocaml/stublibs/*.so.owner


%files devel
%defattr(-,root,root,-)
%doc LICENSE README
%if %opt
%{_libdir}/ocaml/*/*.a
%{_libdir}/ocaml/*/*.cmxa
%{_libdir}/ocaml/*/*.cmx
%endif
%{_libdir}/ocaml/*/*.mli


%changelog
