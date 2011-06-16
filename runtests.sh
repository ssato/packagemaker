#! /bin/bash
set -e


topdir=${0%/*}

if test $# -gt 1; then
    PYTHONPATH=$topdir nosetests -c $topdir/tests/nose.cfg $@
else
    PYTHONPATH=$topdir nosetests -c $topdir/tests/nose.cfg -w $topdir/tests/
fi
