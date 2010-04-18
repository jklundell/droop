#!/bin/sh
#
#  run nose with coverage
#
#  http://somethingaboutorange.com/mrl/projects/nose/0.11.3/testing.html
#  http://somethingaboutorange.com/mrl/projects/nose/0.11.3/plugins/cover.html
#  http://nedbatchelder.com/code/coverage/
#
NOSETESTS=/usr/local/bin/nosetests
$NOSETESTS --with-coverage --cover-package=droop --cover-erase
