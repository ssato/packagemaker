#! /bin/sh

dir=examples
log=$dir/01-simple-filelist-read-from-stdin.log

exec 1> $log 2>&1

set -x


#PYTHONPATH=. cat $dir/simple-files.list | python tools/pmaker -n sysdata -w /tmp/1 --no-mock -
cat $dir/simple-files.list | pmaker -n sysdata --pversion 0.1 -w /tmp/1 --no-mock -
ls /tmp/0
ls /tmp/1/sysdata-0.1/
rpm -qlp /tmp/1/sysdata-0.1/sysdata-0.1-1.*.noarch.rpm
rpm -qlp /tmp/1/sysdata-0.1/sysdata-overrides-0.1-1.*.noarch.rpm
