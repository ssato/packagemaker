#! /bin/sh

id=6
dir=examples
log=$dir/0$id-single-file-relations-buildrpm-backend.log
workdir=/tmp/$id

exec 1> $log 2>&1

set -x


test -d $workdir || mkdir -p $workdir
echo /etc/resolv.conf > $workdir/files.list
pmaker -n resolvconf --pversion 0.1 -w /tmp/$id -vv --no-mock \
        --backend buildrpm.rpm \
        --relations "requires:bash,zsh;obsoletes:sysdata;conflicts:foo" \
        $workdir/files.list
ls /tmp/$id
ls /tmp/$id/resolvconf-0.1/
sed -nr '/^[A-Z][a-z]+:/p' /tmp/$id/resolvconf-0.1/resolvconf.spec
rpm -qlp /tmp/$id/resolvconf-0.1/resolvconf-0.1-1.*.noarch.rpm
