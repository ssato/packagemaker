# For Haskell Packaging Guidelines see:
# - https://fedoraproject.org/wiki/Packaging:Haskell
# - https://fedoraproject.org/wiki/PackagingDrafts/Haskell

Name:           #{name}
Version:        #{version}
Release:        0%{?dist}
Summary:        #{summary}
Group:          #{ _context.get("group", "System Environment/Libraries") }
License:        #{license}
# BEGIN cabal2spec
URL:            http://hackage.haskell.org/package/%{name}
Source0:        http://hackage.haskell.org/packages/archive/%{name}/%{version}/%{name}-%{version}.tar.gz
ExclusiveArch:  %{ghc_arches}
BuildRequires:  ghc-Cabal-devel
BuildRequires:  ghc-rpm-macros
# END cabal2spec
<?py if _context.get("dependencies"): ?>
# list ghc-*-devel dependencies:
BuildRequires:  #{dependencies}
<?py #endif ?>


%description
#{description}


%prep
%setup -q


%build
#%define cabal_configure_options -f "opt1 -opt2 ..."
%ghc_bin_build


%install
%ghc_bin_install


%files
%doc LICENSE
%attr(755,root,root) %{_bindir}/%{name}


%changelog
