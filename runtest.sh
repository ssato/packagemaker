#! /bin/bash
set -e


topdir=${0%/*}

which pep8 2>&1 > /dev/null && check_with_pep8=1 || check_with_pep8=0

if test $# -gt 0; then
    test $check_with_pep8 = 1 && (for x in $@; do pep8 ${x%%:*}; done) || :
    PYTHONPATH=$topdir nosetests -c $topdir/nose.cfg $@
else
    for f in $(cat $topdir/test.targets); do 
        PYTHONPATH=$topdir nosetests -c $topdir/nose.cfg $@
    done
fi
