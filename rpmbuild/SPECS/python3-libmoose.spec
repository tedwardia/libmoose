%define libmoose_release 1
%define libmoose_version 0.1

Name:           python3-libmoose
Version:        %{libmoose_version}
Release:        %{libmoose_release}%{dist}
Summary:        wrappers and helper functions for working with moose (ELK) stack

License:        none
URL:            N/A
Source:         libmoose-%{libmoose_version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:  python3-PyYAML
Requires:  python3-requests
Requires:  python3-elasticsearch


%description
python wrappers and helper functions for working with Moose (ELK stack)

%prep
%setup -n libmoose-%{libmoose_version}

%build
%py3_build

%install
%py3_install

%files -n python3-libmoose
%{python3_sitelib}/libmoose/
%{python3_sitelib}/libmoose-%{libmoose_version}-py%{python3_version}.egg-info

%changelog
* Mon Dec 30 2024 Teddy Wells <twells@nexcess.net> - 0.1.0-1
- Initial package
