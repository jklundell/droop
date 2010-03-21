#!/usr/bin/env python
'''
Count election using Droop's Minneapolis rule

copyright 2010 by Jonathan Lundell
'''

import sys, os
import droop

if len(sys.argv) != 2:
    print >>sys.stderr, "usage: %s ballot_file" % os.path.basename(sys.argv[0])
    sys.exit(1)
print droop.main(dict(rule='mpls', path=sys.argv[1]))

sys.exit(0)