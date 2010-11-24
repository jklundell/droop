#!/bin/sh
#
#  run nose with optional coverage
#
#  http://pypi.python.org/pypi/nose
#  http://pypi.python.org/pypi/coverage
#  http://somethingaboutorange.com/mrl/projects/nose/0.11.3/testing.html
#  http://somethingaboutorange.com/mrl/projects/nose/0.11.3/plugins/cover.html
#  http://nedbatchelder.com/code/coverage/
#  http://bitbucket.org/ned/coveragepy/issues
#
NOSETESTS=nosetests
if [ "$1" = "cover" ]; then
	$NOSETESTS --with-coverage --cover-package=droop --cover-erase
elif [ "$1" = "coverx" ]; then
	$NOSETESTS --processes=4 --with-coverage --cover-package=droop --cover-erase
else
	$NOSETESTS --processes=4
fi
