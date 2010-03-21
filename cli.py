#!/usr/bin/env python
'''
Count election using OpenDroop

copyright 2010 by Jonathan Lundell
'''

import sys, os, getopt
path = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path: sys.path.insert(0, path)

#######################################################################
#
#   Count an election
#
#######################################################################

from modules.profile import ElectionProfile
from droop import Election

class UsageError(Exception):
    "command-line usage error"

rules = ['wigm', 'meek', 'warren', 'mpls']
reportNames = None

usage = """
Usage:

  droop.py [-a arith] [-p prec] [-r report] [-t tiebreak] [-w weaktie] 
                 [-P] [-x reps] rule ballotfile

  -h: print this message
  -a: override default arithmetic: fixed, qx, rational, integer
  -p: override default precision (in digits)
  -g: override guard precision (in digits, qx only)
  -e: override epsilon (in digits, meek/warren)
  -r: report format: tbd
  -t: strong tie-break method: random
  -w: weak tie-break method: tbd
  -P: profile and send output to profile.out
  -x: specify repeat count (for profiling)

  Runs an election for the given election rule and ballot file.
  Results are printed to stdout.
  The following methods are available:
  %s
""" % ", ".join(rules)


try:
    # Parse the command line.
    (opts, args) = getopt.getopt(sys.argv[1:], "Pha:p:g:e:r:t:w:x:")

    doProfile = False
    reps = 1
    prec = None
    guard = None
    arithmetic = None
    epsilon = None
    
    for o, a in opts:
        if o == "-r":
              if a in reportNames:
                  reportformat = a
              else: raise UsageError("Unrecognized report format '%s'" % a)
        if o == "-a":
              if a in ["fixed", "qx", "quasi-exact", "rational", "integer"]:
                  arithmetic = a
              else: raise UsageError("Unrecognized arithmetic '%s'" % a)
        if o == "-p":
              prec = int(a)
        if o == "-g":
              guard = int(a)
        if o == "-e":
              epsilon = int(a)
        if o == "-t":
              if a in ["random", "alpha", "index"]:
                  strongTieBreakMethod = a
              else: raise UsageError("Unrecognized tie-break method '%s'" % a)
        if o == "-w":
              if a in ["strong", "forward", "backward"]:
                  weakTieBreakMethod = a
              else: raise UsageError("Unrecognized weak tie-break method '%s'" % a)
        if o == "-P":
              import cProfile
              import pstats
              doProfile = True
              profilefile = "profile.out"
        if o == "-x":
              reps = int(a)
        if o == "-h": raise UsageError('-h')
    
    if len(args) == 1:
        ruleName = 'meek'  # handy default for testing
        bltPath = args[0]
    elif len(args) != 2:
        if len(args) < 2: raise UsageError("Specify rule and ballot file")
        else: raise UsageError("Too many arguments")
    else:
        ruleName = args[0]
        bltPath = args[1]

    options=dict(arithmetic=arithmetic, precision=prec, guard=guard, epsilon=epsilon)
    if ruleName == 'warren':
        rule = 'meek'
        options['variant'] = 'warren'
    elif ruleName in rules:
        rule = ruleName
    else: raise UsageError("Unrecognized rule '%s'" % ruleName)

except getopt.GetoptError as err:
    print >>sys.stderr, str(err) # will print something like "option -q not recognized"
    print >>sys.stderr, usage
    sys.exit(1)
except UsageError as err:
    if str(err) == '-h':
        print >>sys.stderr, usage
        sys.exit(0)
    print >>sys.stderr, str(err)
    print >>sys.stderr, usage
    sys.exit(1)

_rule = __import__('modules.rules.%s' % rule, globals(), locals(), ['Rule'], -1)
Rule = _rule.Rule

#####################
#
#  Run the election
#
#####################
def doElection(reps=1):
    "run election with repeat count for profiling"
    electionProfile = ElectionProfile(path=bltPath)
    intr = False
    for i in xrange(reps):
        E = Election(Rule, electionProfile, options=options)
        try:
            E.count()    # repeat for profiling
        except KeyboardInterrupt:
            intr = True
    print E.report(intr)    # election report
    print "\nDump:\n"
    print E.dump()      # round-by-round dump

try:
    if doProfile:
        cProfile.run('E = doElection(reps)', profilefile)
    else:
        E = doElection()
except ElectionProfile.ElectionProfileError as err:
    print >>sys.stderr, "**Election profile error: %s" % str(err)
    sys.exit(2)
except Election.ElectionError as err:
    print >>sys.stderr, "**Election error: %s" % str(err)
    sys.exit(2)

if doProfile:
    p = pstats.Stats(profilefile)
    p.strip_dirs().sort_stats('time').print_stats(50)
