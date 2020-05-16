#!/bin/sh
#
#  run from test/
#  run pytest with optional coverage
#
PYTEST=pytest

if [ "$1" = "cover" ]; then
	$PYTEST --cov-report term-missing --cov=droop
else
	$PYTEST
fi
