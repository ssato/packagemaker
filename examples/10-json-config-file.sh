#! /bin/sh

id=10
dir=$(dirname $0)
pname="sysdata"
log=$dir/$id-json-config-file.log
workdir=/tmp/$id
config=$dir/config_00.json

exec 1> $log 2>&1

set -x


test -d $workdir || mkdir -p $workdir
pmaker -w $workdir -C $config
ls $workdir
ls $workdir/$pname-0.1/
sed -nr '/^[A-Z][a-z]+:/p' $workdir/$pname-0.1/$pname.spec
rpm -qlp $workdir/$pname-0.1/$pname-0.1-1.*.noarch.rpm
