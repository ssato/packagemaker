#! /bin/sh

dir=examples
log=$dir/04-single-file-destdir-buildrpm-backend.log

exec 1> $log 2>&1

set -x


echo $dir/etc/resolv.conf | \
  pmaker -n resolvconf --pversion 0.1 -w /tmp/4 -vv --no-mock \
        --destdir $dir --backend buildrpm.rpm -
ls /tmp/4
ls /tmp/4/resolvconf-0.1/
rpm -qlp /tmp/4/resolvconf-0.1/resolvconf-0.1-1.*.noarch.rpm
