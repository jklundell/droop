#!/usr/bin/env python
'''
Count election using the Academy Awards nominating rule

copyright 2010 by Jonathan Lundell
'''

import sys, os
import droop

if len(sys.argv) != 2:
    print >>sys.stderr, "usage: %s ballot_file" % os.path.basename(sys.argv[0])
    sys.exit(1)
print droop.main(dict(rule='wigm', path=sys.argv[1], arithmetic='fixed', precision=2, integer_quota=True, defeat_zero=True))

sys.exit(0)
