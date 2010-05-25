#!/bin/sh
#
#  run nose with optional coverage
#
#  http://somethingaboutorange.com/mrl/projects/nose/0.11.3/testing.html
#  http://somethingaboutorange.com/mrl/projects/nose/0.11.3/plugins/cover.html
#  http://nedbatchelder.com/code/coverage/
#  http://bitbucket.org/ned/coveragepy/issues
#
NOSETESTS=/usr/local/bin/nosetests
if [ "$1" = "cover" ]; then
	$NOSETESTS --with-coverage --cover-package=droop --cover-erase 
elif [ "$1" = "cover" ]; then
	$NOSETESTS --processes=4 -v
else
	$NOSETESTS --processes=4
fi
