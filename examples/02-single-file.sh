#! /bin/sh

dir=examples
log=$dir/02-single-file.log

exec 1> $log 2>&1

set -x


echo /etc/resolv.conf | \
  PYTHONPATH=. \
  python tools/pmaker -n resolvconf -w /tmp/2 -vv --no-mock -
ls /tmp/2
ls /tmp/2/resolvconf-0.1/
rpm -qlp /tmp/2/resolvconf-0.1/resolvconf-0.1-1.*.noarch.rpm
