#! /bin/bash
set -ex

dir=${0%/*}

test -f $dir/00-simple-filelist.log || \
$dir/00-simple-filelist.sh && \
sed -i 's,^\+,$,g' $dir/00-simple-filelist.log

test -f $dir/01-simple-filelist-read-from-stdin.log || \
$dir/01-simple-filelist-read-from-stdin.sh &&
sed -i '/^. cat examples/d; /^. PYTHON/d; s,^. python ,$ cat examples/simple-files.list | python ,; s,^\+,$,g' \
    $dir/01-simple-filelist-read-from-stdin.log

test -f $dir/02-single-file.log || \
$dir/02-single-file.sh && \
sed -i '/^. echo \/etc\/resolv.conf/d; /^. PYTHON/d; s,^. python ,$ echo /etc/resolv.conf | python ,; s,^\+,$,g' $dir/02-single-file.log

test -f $dir/03-single-file-destdir.log || \
$dir/03-single-file-destdir.sh && \
sed -i '/^. echo .*\/etc\/resolv.conf/d; /^. PYTHON/d; s,^. python ,$ echo examples/etc/resolv.conf | python ,; s,^\+,$,g' $dir/03-single-file-destdir.log

test -f $dir/05-advanced-filelist.log || \
$dir/05-advanced-filelist.sh && \
sed -i 's,^\+,$,g' $dir/05-advanced-filelist.log
