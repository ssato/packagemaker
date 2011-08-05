#! /bin/bash
set -e


topdir=${0%/*}

if test $# -gt 0; then
    PYTHONPATH=$topdir nosetests -c $topdir/nose.cfg $@
else
    PYTHONPATH=$topdir nosetests -c $topdir/nose.cfg -w $topdir/tests/
fi
