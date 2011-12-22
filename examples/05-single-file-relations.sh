#! /bin/sh

id=5
dir=examples
log=$dir/0$id-single-file-relations.log

exec 1> $log 2>&1

set -x


echo /etc/resolv.conf | \
  pmaker -n resolvconf --pversion 0.1 -w /tmp/$id -vv --no-mock \
        --relations "requires:bash,zsh;obsoletes:sysdata;conflicts:foo" \
        -
ls /tmp/$id
ls /tmp/$id/resolvconf-0.1/
sed -nr '/^[A-Z][a-z]+:/p' /tmp/$id/resolvconf-0.1/resolvconf.spec
rpm -qlp /tmp/$id/resolvconf-0.1/resolvconf-0.1-1.*.noarch.rpm
