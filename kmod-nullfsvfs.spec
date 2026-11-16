%global	kmod_name nullfsvfs
%global	debug_package %{nil}

# Build flags are inherited from the kernel
%undefine _auto_set_build_flags

# %%bcond is not available in el8's RPM 4.14
%if 0%{?rhel} == 8
%bcond_without kabi
%endif
%if 0%{?rhel} >= 9
%bcond kabi 1
%endif

# kABI kernel modules only on RHEL
%if 0%{?fedora}
%bcond kabi 0
%endif

%{!?kversion: %global kversion %(uname -r)}

Name:           kmod-%{kmod_name}
Version:        0.28
Release:        1%{?dist}
Summary:        A virtual file system that behaves like /dev/null
License:        GPLv3+
URL:            https://github.com/abbbi/%{kmod_name}

Source0:        %{url}/archive/v%{version}.tar.gz#/%{kmod_name}-%{version}.tar.gz
%if 0%{?rhel} == 9
# https://github.com/abbbi/nullfsvfs/commit/63661607ded4e3ee0ba35cf50e1166a2b203daeb
Patch0:         %{kmod_name}-el9.patch
%endif
%if 0%{?rhel} == 10
# EL 10.3+ backports the Linux 6.15 inode_operations->mkdir() change
Patch1:         %{kmod_name}-el10.patch
%endif

BuildRequires:  elfutils-libelf-devel
BuildRequires:  gcc
BuildRequires:  kernel-devel
BuildRequires:  kernel-rpm-macros
BuildRequires:  kmod
BuildRequires:  redhat-rpm-config

Provides:       %{kmod_name}-kmod = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       module-init-tools

Obsoletes:      kmod-nullfs < %{?epoch:%{epoch}:}%{version}-%{release}

%if %{with kabi}
BuildRequires:  kernel-abi-stablelists
Provides:       kabi-modules = %{kversion}
%else
Requires:       kernel-uname-r = %{kversion}
%endif

%description
A virtual file system that behaves like /dev/null. It can handle regular file
operations but writing to files does not store any data. The file size is
however saved, so reading from the files behaves like reading from /dev/zero
with a fixed size.

Writing and reading is basically an NOOP, so it can be used for performance
testing with applications that require directory structures.

This package provides the %{kmod_name} kernel module(s) built for the Linux kernel
using the family of processors.

%prep
%autosetup -p1 -n %{kmod_name}-%{version}

%build
make -C %{_usrsrc}/kernels/%{kversion} M=$PWD modules

%install
export INSTALL_MOD_PATH=%{buildroot}%{_prefix}
export INSTALL_MOD_DIR=extra/%{kmod_name}
make -C %{_usrsrc}/kernels/%{kversion} M=$PWD modules_install

%if %{with kabi}
install -d %{buildroot}%{_sysconfdir}/depmod.d/
echo "override %{kmod_name} * weak-updates/%{kmod_name}" > %{buildroot}%{_sysconfdir}/depmod.d/kmod-%{kmod_name}.conf
%endif

# Remove the unrequired files.
rm -f %{buildroot}%{_prefix}/lib/modules/%{kversion}/modules.*

find %{buildroot} -type f -name '*.ko' | xargs %{__strip} --strip-debug
find %{buildroot} -type f -name '*.ko' | xargs xz

%if %{with kabi}

%post
if [ -e "/boot/System.map-%{kversion}" ]; then
    %{_sbindir}/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(find %{_prefix}/lib/modules/%{kversion}/extra/%{kmod_name} | grep '\.ko.xz$') )
if [ -x "%{_sbindir}/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | %{_sbindir}/weak-modules --add-modules
fi

%preun
rpm -ql kmod-%{kmod_name}-%{version}-%{release} | grep '\.ko.xz$' > %{_var}/run/rpm-kmod-%{kmod_name}-modules

%postun
if [ -e "/boot/System.map-%{kversion}" ]; then
    %{_sbindir}/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(cat %{_var}/run/rpm-kmod-%{kmod_name}-modules) )
rm %{_var}/run/rpm-kmod-%{kmod_name}-modules
if [ -x "%{_sbindir}/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | %{_sbindir}/weak-modules --remove-modules
fi

%else

%post
if [ -e "/boot/System.map-%{kversion}" ]; then
    %{_sbindir}/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi

%postun
if [ -e "/boot/System.map-%{kversion}" ]; then
    %{_sbindir}/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi

%endif

%files
%license LICENSE
%{_prefix}/lib/modules/%{kversion}/extra/*
%if %{with kabi}
%config %{_sysconfdir}/depmod.d/kmod-%{kmod_name}.conf
%endif

%changelog
* Mon Nov 16 2026 Simone Caronni <negativo17@gmail.com> - 0.28-1
- Update to 0.28.
- Fix build on EL 10.3+.
- Build kABI kernel modules only on RHEL.

* Wed Jul 01 2026 Simone Caronni <negativo17@gmail.com> - 0.27-1
- Update to 0.27.

* Sun Mar 08 2026 Simone Caronni <negativo17@gmail.com> - 0.26-1
- Rename to nullfsvfs and update to 0.26.

* Mon Feb 09 2026 Simone Caronni <negativo17@gmail.com> - 0.22-1
- Update to 0.22.

* Mon Dec 01 2025 Simone Caronni <negativo17@gmail.com> - 0.21-1
- Update to 0.21.

* Wed Jun 18 2025 Simone Caronni <negativo17@gmail.com> - 0.19-1
- Update to 0.19.

* Wed Apr 16 2025 Simone Caronni <negativo17@gmail.com> - 0.18-1
- Update to 0.18.

* Wed Mar 12 2025 Simone Caronni <negativo17@gmail.com> - 0.17-8
- Rename source package from nvidia-kmod to kmod-nvidia, the former is now used
  for the akmods variant.
- Use /usr/lib/modules for installing kernel modules and not /lib/modules.
- Trim changelog.
- Drop compress macro and just add a step during install.

* Wed Sep 25 2024 Simone Caronni <negativo17@gmail.com> - 0.17-7
- Rebuild.

* Wed Jun 05 2024 Simone Caronni <negativo17@gmail.com> - 0.17-6
- Rebuild for latest kernel.

* Mon Jun 03 2024 Simone Caronni <negativo17@gmail.com> - 0.17-5
- Add patch for EL 9.4 kernel backports.

* Wed Apr 03 2024 Simone Caronni <negativo17@gmail.com> - 0.17-4
- Sync uname -r with kversion passed from scripts.

* Wed Apr 03 2024 Simone Caronni <negativo17@gmail.com> - 0.17-3
- Rebuild.
