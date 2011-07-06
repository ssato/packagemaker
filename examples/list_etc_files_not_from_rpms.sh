#! /bin/sh

logfile=$1

list_files () {
    local dir=$1
    find $dir -type f
}

is_not_from_rpm () {
    local f=$1
    LANG=C rpm -qf $f | grep -q 'is not owned' 2>/dev/null
}

(
for f in $(list_files /etc)
do
    is_not_from_rpm $f && echo $f
done
) > $logfile
