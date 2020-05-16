#!/bin/sh
#
#  run from test/
#  run pylint on droop
#
CWD=`pwd`
CWD=`basename $CWD`
if [ "$CWD" != "test" ]; then
    echo "run from test/"
    exit
fi
cd ..
pylint "--msg-template={path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
    --disable=C0103,R0801,R0902,R0904,R0912,R0913,R0914,R0915,R0921,W0212,W0223,W0231,W0631 \
	Droop.py droop test/common.py test/test_*.py
