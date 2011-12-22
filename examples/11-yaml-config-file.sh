#! /bin/sh

id=11
dir=$(dirname $0)
pname="sysdata"
log=$dir/$id-yaml-config-file.log
workdir=/tmp/$id
config=$dir/config_01.yaml

exec 1> $log 2>&1

set -x


test -d $workdir || mkdir -p $workdir
pmaker -w $workdir -C $config
ls $workdir
ls $workdir/$pname-0.0.2/
sed -nr '/^[A-Z][a-z]+:/p' $workdir/$pname-0.0.2/$pname.spec
rpm -qlp $workdir/$pname-0.0.2/$pname-0.0.2-3.*.noarch.rpm
rpm -qlp $workdir/$pname-0.0.2/$pname-overrides-0.0.2-3.*.noarch.rpm
