#!/bin/sh
#
#  run from test/
#  run pyflakes on *.py
#
CWD=`pwd`
CWD=`basename $CWD`
if [ "$CWD" != "test" ]; then
    echo "run from test/"
fi
find .. -name '*.py' | xargs pyflakes
