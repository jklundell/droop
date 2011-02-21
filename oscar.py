#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Count election using the Academy Awards nominating rule

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


    This is an approximation of the STV rule used by the Academy for
    best-picture nominations. Some references:
    http://www.thewrap.com/deal-central/column-post/revealed-how-oscar-nominee-ballots-are-counted-12279
    http://oscarvotes123.blogspot.com/
    http://insidemovies.ew.com/2011/01/27/oscar-voter-ballot-reader-poll-results/
    
    According to these references, the quota is recalculated on each round,
    and, at least after the first surplus distribution, candidates with less
    than 1% of the vote are defeated.
'''
import sys, os
import Droop
import droop

def usage():
    "oscar usage string"
    return "usage: %s ballot_file" % os.path.basename(sys.argv[0])

if len(sys.argv) != 2:
    print >>sys.stderr, usage()
    sys.exit(1)
try:
    print Droop.main(dict(rule='wigm', path=sys.argv[1], arithmetic='fixed', precision=2, integer_quota=True, defeat_batch='zero'))
except (droop.common.UsageError, droop.common.ElectionError, droop.profile.ElectionProfileError) as err:
    print >>sys.stderr, "** oscar: %s" % err
    print >>sys.stderr, usage()
    sys.exit(1)
sys.exit(0)
