#
%define work_dir /opt/gateway

%define nginx_home %{work_dir}/
%define nginx_user gateway
%define nginx_group gateway
%define nginx_loggroup adm


# distribution specific definitions
%define use_systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7) || (0%{?suse_version} == 1315)

%if 0%{?rhel} == 6
%define _group System Environment/Daemons
Requires(pre): shadow-utils
Requires: initscripts >= 8.36
Requires(post): chkconfig
Requires: openssl >= 1.0.1
BuildRequires: openssl-devel >= 1.0.1
%endif

%if 0%{?rhel} == 7
BuildRequires: redhat-lsb-core
%define _group System Environment/Daemons
%define epoch 1
Epoch: %{epoch}
Requires(pre): shadow-utils
Requires: systemd
BuildRequires: systemd
%define os_minor %(lsb_release -rs | cut -d '.' -f 2)
%if %{os_minor} >= 4
Requires: openssl >= 1.0.2
BuildRequires: openssl-devel >= 1.0.2
%define dist .el7_4
%else
Requires: openssl >= 1.0.1
BuildRequires: openssl-devel >= 1.0.1
%define dist .el7
%endif
%endif

%if 0%{?suse_version} == 1315
%define _group Productivity/Networking/Web/Servers
%define nginx_loggroup trusted
Requires(pre): shadow
Requires: systemd
BuildRequires: libopenssl-devel
BuildRequires: systemd
%endif

# end of distribution specific definitions

%define main_version 1.13.10
%define main_release 1%{?dist}.ngx

%define bdir %{_builddir}/%{name}-%{main_version}

%define WITH_CC_OPT $(echo %{optflags} $(pcre-config --cflags)) -fPIC
%define WITH_LD_OPT -Wl,-z,relro -Wl,-z,now -pie

%define BASE_CONFIGURE_ARGS $(echo "--prefix=/opt/gateway/nginx --sbin-path=/opt/gateway/sbin/nginx --modules-path=/opt/gateway/usr/lib/nginx/modules --conf-path=/opt/gateway/nginx/nginx.conf --error-log-path=/opt/gateway/var/log/error.log --http-log-path=/opt/gateway/var/log/access.log --pid-path=/opt/gateway/run/nginx.pid --lock-path=/opt/gateway/run/nginx.lock --http-client-body-temp-path=%{work_dir}/cache/nginx/client_temp --http-proxy-temp-path=%{work_dir}/cache/nginx/proxy_temp --http-fastcgi-temp-path=%{work_dir}/cache/nginx/fastcgi_temp --http-uwsgi-temp-path=%{work_dir}/cache/nginx/uwsgi_temp --http-scgi-temp-path=%{work_dir}/cache/nginx/scgi_temp --user=%{nginx_user} --group=%{nginx_group} --with-compat --with-file-aio --with-threads --with-http_addition_module --with-http_auth_request_module --with-http_dav_module --with-http_flv_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_mp4_module --with-http_random_index_module --with-http_realip_module --with-http_secure_link_module --with-http_slice_module --with-http_ssl_module --with-http_stub_status_module --with-http_sub_module --with-http_v2_module --with-mail --with-mail_ssl_module --with-stream --with-stream_realip_module --with-stream_ssl_module --with-stream_ssl_preread_module")

Summary: High performance web server
Name: nginx-letters
Version: %{main_version}
Release: %{main_release}
Vendor: Nginx, Inc.
URL: http://nginx.org/
Group: %{_group}

Source0: http://nginx.org/download/%{name}-%{version}.tar.gz
Source1: logrotate
Source2: nginx.init.in
Source3: nginx.sysconf
Source4: nginx.conf
Source5: nginx.vh.default.conf
Source7: nginx-debug.sysconf
Source8: nginx-letters.service
Source9: nginx.upgrade.sh
Source10: nginx.suse.logrotate
Source11: nginx-debug.service
Source12: COPYRIGHT
Source13: nginx.check-reload.sh

Source14: ndk_http_module.so
Source15: ngx_http_lua_module.so

License: 2-clause BSD-like license

BuildRoot: %{_tmppath}/%{name}-%{main_version}-%{main_release}-root
BuildRequires: zlib-devel
BuildRequires: pcre-devel

Provides: webserver

%description
nginx [engine x] is an HTTP and reverse proxy server, as well as
a mail proxy server.

%if 0%{?suse_version} == 1315
%debug_package
%endif

%prep
%setup -q
cp %{SOURCE2} .
sed -e 's|%%DEFAULTSTART%%|2 3 4 5|g' -e 's|%%DEFAULTSTOP%%|0 1 6|g' \
    -e 's|%%PROVIDES%%|nginx|g' < %{SOURCE2} > nginx.init
sed -e 's|%%DEFAULTSTART%%||g' -e 's|%%DEFAULTSTOP%%|0 1 2 3 4 5 6|g' \
    -e 's|%%PROVIDES%%|nginx-debug|g' < %{SOURCE2} > nginx-debug.init

%build
./configure %{BASE_CONFIGURE_ARGS} \
    --with-openssl=/tmp/letters-gateway/openssl-1.1.0f \
    --with-openssl-opt=enable-ec_nistp_64_gcc_128 \
    --with-openssl-opt=no-nextprotoneg \
    --with-openssl-opt=no-weak-ssl-ciphers \
    --with-openssl-opt=no-ssl3 \
    --with-zlib=/tmp/letters-gateway/zlib-1.2.11 \
    --add-dynamic-module=/tmp/letters-gateway/ngx_devel_kit-0.3.0 \
    --add-dynamic-module=/tmp/letters-gateway/lua-nginx-module-0.10.13 \
    --with-debug

make %{?_smp_mflags}

%install
%{__rm} -rf $RPM_BUILD_ROOT
%{__make} DESTDIR=$RPM_BUILD_ROOT INSTALLDIRS=vendor install

%{__mkdir} -p $RPM_BUILD_ROOT%{work_dir}/var/log
%{__mkdir} -p $RPM_BUILD_ROOT%{work_dir}/run

%{__mkdir} -p $RPM_BUILD_ROOT%{work_dir}/usr/share/nginx
%{__mv} $RPM_BUILD_ROOT%{work_dir}/nginx/html $RPM_BUILD_ROOT%{work_dir}/usr/share/nginx

%{__rm} -f $RPM_BUILD_ROOT%{work_dir}/nginx/*.default
%{__rm} -f $RPM_BUILD_ROOT%{work_dir}/nginx/fastcgi.conf

#%{__mkdir} -p $RPM_BUILD_ROOT%{_localstatedir}/log/nginx
#%{__mkdir} -p $RPM_BUILD_ROOT%{_localstatedir}/run/nginx
%{__mkdir} -p $RPM_BUILD_ROOT%{work_dir}/cache/nginx

%{__mkdir} -p $RPM_BUILD_ROOT%{work_dir}/usr/lib/nginx/modules
%{__install} -m 644 -p %{SOURCE14} \
    $RPM_BUILD_ROOT%{work_dir}/usr/lib/nginx/modules/ndk_http_module.so
%{__install} -m 644 -p %{SOURCE15} \
    $RPM_BUILD_ROOT%{work_dir}/usr/lib/nginx/modules/ngx_http_lua_module.so

#cd $RPM_BUILD_ROOT%{work_dir}/nginx && \
#    %{__ln_s} ../..%{work_dir}/usr/lib/nginx/modules modules && cd -

#%{__mkdir} -p $RPM_BUILD_ROOT%{_datadir}/doc/%{name}-%{main_version}
#%{__install} -m 644 -p %{SOURCE12} \
#    $RPM_BUILD_ROOT%{_datadir}/doc/%{name}-%{main_version}/

%{__mkdir} -p $RPM_BUILD_ROOT%{work_dir}/nginx/conf.d
%{__rm} $RPM_BUILD_ROOT%{work_dir}/nginx/nginx.conf
%{__install} -m 644 -p %{SOURCE4} \
    $RPM_BUILD_ROOT%{work_dir}/nginx/nginx.conf
%{__install} -m 644 -p %{SOURCE5} \
    $RPM_BUILD_ROOT%{work_dir}/nginx/conf.d/default.conf

#%{__mkdir} -p $RPM_BUILD_ROOT%{work_dir}/sysconfig
#%{__install} -m 644 -p %{SOURCE3} \
#    $RPM_BUILD_ROOT%{work_dir}/sysconfig/nginx

#%{__install} -p -D -m 0644 %{bdir}/objs/nginx.8 \
#    $RPM_BUILD_ROOT%{_mandir}/man8/nginx.8

%if %{use_systemd}
# install systemd-specific files
%{__mkdir} -p $RPM_BUILD_ROOT%{_unitdir}
%{__install} -m644 %SOURCE8 \
    $RPM_BUILD_ROOT%{_unitdir}/nginx-letters.service
%{__mkdir} -p $RPM_BUILD_ROOT%{_libexecdir}/initscripts/legacy-actions/nginx
%{__install} -m755 %SOURCE9 \
    $RPM_BUILD_ROOT%{_libexecdir}/initscripts/legacy-actions/nginx/upgrade
%{__install} -m755 %SOURCE13 \
    $RPM_BUILD_ROOT%{_libexecdir}/initscripts/legacy-actions/nginx/check-reload
%else
# install SYSV init stuff
%{__mkdir} -p $RPM_BUILD_ROOT%{_initrddir}
%{__install} -m755 nginx.init $RPM_BUILD_ROOT%{_initrddir}/nginx
%endif

# install log rotation stuff
%{__mkdir} -p $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d
%if 0%{?suse_version}
%{__install} -m 644 -p %{SOURCE10} \
    $RPM_BUILD_ROOT%{work_dir}/logrotate.d/nginx
%else
%{__install} -m 644 -p %{SOURCE1} \
    $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/nginx
%endif

%clean
%{__rm} -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root)

#%{work_dir}/nginx

%dir %{work_dir}/nginx
%dir %{work_dir}/nginx/conf.d
%{work_dir}/usr/lib/nginx/modules
%{work_dir}/sbin/nginx
%dir %{work_dir}/var/log
%dir %{work_dir}/run
%dir %{work_dir}/usr/share/nginx/html
%{work_dir}/usr/share/nginx/html/*

%config(noreplace) %{work_dir}/nginx/nginx.conf
%config(noreplace) %{work_dir}/nginx/conf.d/default.conf
%config(noreplace) %{work_dir}/nginx/mime.types
%config(noreplace) %{work_dir}/nginx/fastcgi_params
%config(noreplace) %{work_dir}/nginx/scgi_params
%config(noreplace) %{work_dir}/nginx/uwsgi_params
%config(noreplace) %{work_dir}/nginx/koi-utf
%config(noreplace) %{work_dir}/nginx/koi-win
%config(noreplace) %{work_dir}/nginx/win-utf

%config(noreplace) %{_sysconfdir}/logrotate.d/nginx
#%config(noreplace) %{work_dir}/sysconfig/nginx
%if %{use_systemd}
%{_unitdir}/nginx-letters.service
%dir %{_libexecdir}/initscripts/legacy-actions/nginx
%{_libexecdir}/initscripts/legacy-actions/nginx/*
%else
%{_initrddir}/nginx
%endif

%attr(0755,root,root) %dir %{work_dir}/nginx
%attr(0755,root,root) %dir %{work_dir}/usr/lib/nginx/modules
%dir %{work_dir}/nginx

%attr(0755,root,root) %dir %{work_dir}/cache/nginx
%attr(0755,root,root) %dir %{work_dir}/var/log

#%dir %{_datadir}/doc/%{name}-%{main_version}
#%doc %{_datadir}/doc/%{name}-%{main_version}/COPYRIGHT
#%{_mandir}/man8/nginx.8*

%pre
# Add the "nginx" user
getent group %{nginx_group} >/dev/null || groupadd -r %{nginx_group}
getent passwd %{nginx_user} >/dev/null || \
    useradd -r -g %{nginx_group} -s /sbin/nologin \
    -d %{nginx_home} -c "nginx user"  %{nginx_user}
exit 0

%post
# Register the nginx-letters.service
if [ $1 -eq 1 ]; then
%if %{use_systemd}
    /usr/bin/systemctl preset nginx-letters.service >/dev/null 2>&1 ||:
    /usr/bin/systemctl preset nginx-debug.service >/dev/null 2>&1 ||:
%else
    /sbin/chkconfig --add nginx
    /sbin/chkconfig --add nginx-debug
%endif
    # print site info
    cat <<BANNER

----------------------------------------------------------------------

Thanks for using nginx!

Please find the official documentation for nginx here:
* http://nginx.org/en/docs/

Please subscribe to nginx-announce mailing list to get
the most important news about nginx:
* http://nginx.org/en/support.html

Commercial subscriptions for nginx are available on:
* http://nginx.com/products/

----------------------------------------------------------------------
BANNER

    # Touch and set permisions on default log files on installation

    if [ -d %{work_dir}/log/ ]; then
        if [ ! -e %{work_dir}/var/log/access.log ]; then
            touch %{work_dir}/var/log/access.log
            %{__chmod} 640 %{work_dir}/var/log/access.log
            %{__chown} nginx:%{nginx_loggroup} %{work_dir}/var/log/access.log
        fi

        if [ ! -e %{work_dir}/var/log/error.log ]; then
            touch %{work_dir}/var/log/error.log
            %{__chmod} 640 %{work_dir}/var/log/error.log
            %{__chown} nginx:%{nginx_loggroup} %{work_dir}/var/log/error.log
        fi
    fi
fi

%preun
if [ $1 -eq 0 ]; then
%if %use_systemd
    /usr/bin/systemctl --no-reload disable nginx-letters.service >/dev/null 2>&1 ||:
    /usr/bin/systemctl stop nginx-letters.service >/dev/null 2>&1 ||:
%else
    /sbin/service nginx stop > /dev/null 2>&1
    /sbin/chkconfig --del nginx
    /sbin/chkconfig --del nginx-debug
%endif
fi

%postun
%if %use_systemd
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 ||:
%endif
if [ $1 -ge 1 ]; then
    /sbin/service nginx status  >/dev/null 2>&1 || exit 0
    /sbin/service nginx upgrade >/dev/null 2>&1 || echo \
        "Binary upgrade failed, please check nginx's error.log"
fi
