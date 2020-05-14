#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Count IRV election using Droop's WIGM rule

Copyright 2010 by Jonathan Lundell

This file is part of Droop.

    Droop is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Droop is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Droop.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys, os
import Droop
import droop

def usage():
    "irv usage string"
    return "usage: %s ballot_file" % os.path.basename(sys.argv[0])

if len(sys.argv) != 2:
    print(usage(), file=sys.stderr)
    sys.exit(1)
try:
    print(Droop.main(dict(rule='wigm', arithmetic='integer', path=sys.argv[1])))
except (droop.common.UsageError, droop.common.ElectionError, droop.profile.ElectionProfileError) as err:
    print("** irv: %s" % err, file=sys.stderr)
    print(usage(), file=sys.stderr)
    sys.exit(1)
sys.exit(0)
