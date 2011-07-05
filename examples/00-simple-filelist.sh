#! /bin/sh

dir=examples
log=$dir/00-simple-filelist.log

exec 1> $log 2>&1

set -x

cat $dir/simple-files.list
PYTHONPATH=. python tools/pmaker -n sysdata -w /tmp/0 $dir/simple-files.list
ls /tmp/0
ls /tmp/0/sysdata-0.1/
rpm -qlp /tmp/0/sysdata-0.1/sysdata-0.1-1.fc14.noarch.rpm
rpm -qlp /tmp/0/sysdata-0.1/sysdata-overrides-0.1-1.fc14.noarch.rpm
rpm -qp --scripts /tmp/0/sysdata-0.1/sysdata-overrides-0.1-1.fc14.noarch.rpm
