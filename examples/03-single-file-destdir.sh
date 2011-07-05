#! /bin/sh

dir=examples
log=$dir/03-single-file-destdir.log

exec 1> $log 2>&1

set -x


echo $dir/etc/resolv.conf | \
  PYTHONPATH=. \
  python tools/pmaker -n resolvconf -w /tmp/3 -vv --no-mock --destdir $dir -
ls /tmp/3
ls /tmp/3/resolvconf-0.1/
rpm -qlp /tmp/3/resolvconf-0.1/resolvconf-0.1-1.*.noarch.rpm
