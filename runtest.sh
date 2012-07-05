#! /bin/bash
set -e


topdir=${0%/*}

which pep8 2>&1 > /dev/null && check_with_pep8=1 || check_with_pep8=0

if test $# -gt 0; then
    test $check_with_pep8 = 1 && (for x in $@; do pep8 ${x%%:*}; done) || :
    PYTHONPATH=$topdir nosetests -c $topdir/nose.cfg $@
else
    for f in $(cat $topdir/tests/targets); do 
        echo "## $f"
        test $check_with_pep8 = 1 && pep8 ${f%%:*} || :
        PYTHONPATH=$topdir nosetests -c $topdir/nose.cfg $f
    done
fi
