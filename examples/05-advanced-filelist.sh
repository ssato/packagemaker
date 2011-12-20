#! /bin/sh

dir=examples
log=$dir/05-advanced-filelist.log
list_sh=$dir/list_etc_files_not_from_rpms.sh
listfile=/tmp/5/etc.not_from_package.files
workdir=$(dirname $listfile)

exec 1> $log 2>&1

set -x

mkdir -p $workdir

cat $list_sh
$list_sh $listfile
pmaker -n etcdata --pversion 0.1 -v -w $workdir --stepto sbuild $listfile
ls $workdir/etcdata-0.1/
make -C $workdir/etcdata-0.1/ rpm
rpm -qlp $workdir/etcdata-0.1/etcdata-0.1-1.*.noarch.rpm
