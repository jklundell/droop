#!/usr/bin/env python
'''
Count election using Droop's Minneapolis rule

copyright 2010 by Jonathan Lundell
'''

import sys, os
import Droop

def usage():
    "mpls usage string"
    return "usage: %s ballot_file" % os.path.basename(sys.argv[0])

if len(sys.argv) != 2:
    print >>sys.stderr, usage()
    sys.exit(1)
try:
    print Droop.main(dict(rule='mpls', path=sys.argv[1]))
except Droop.UsageError as err:
    print >>sys.stderr, "** mpls: %s" % err
    print >>sys.stderr, usage()
    sys.exit(1)
sys.exit(0)
