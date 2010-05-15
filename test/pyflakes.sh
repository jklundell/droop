#!/bin/sh
#
#  run pyflakes on *.py
#
find .. -name '*.py' | xargs pyflakes
