#!/usr/bin/env python
'''
Droop external interface

copyright 2010 by Jonathan Lundell


   main(options)

   main is a convenience function for running an election from outside

   options is a dictionary that must, at a minimum, include a path to a ballot file
   It may also include rule parameters and report requests (pending)

   The default rule is 'meek'

   options currently include:
   path=ballot_file_path
   rule=election_rule_name
     variant=warren to switch meek to warren mode
     epsilon=<set meek surplus limit to 10^-epsilon>
   report= [not currently suppported]
   arithmetic=quasi-exact|fixed|integer|rational
     (integer is fixed with precision=0)
     precision=<precision for fixed or qx in digits>
     guard=<guard for qx in digits>
     dp=<display precision (digits) for rational>
'''
   
import sys
from packages.profile import ElectionProfile
from packages.election import Election
import packages.rules
import packages.values

class UsageError(Exception):
    "command-line usage error"

E = None

def main(options=None):
    "run an election"

    if not options:
        raise UsageError("no ballot file specified")

    #  process options
    #
    #  we know about (rule, path, profile)
    #  all the others are passed to the various consumers
    #
    rule = 'meek'       # default rule
    path = None         # ballot path must be specified
    doProfile = False   # performance profiling
    reps = 1            # repetitions (for profiling)
    for opt,arg in options.items():
        if opt == 'rule':       # rule=<election rule name> default: 'meek'
            rule = arg
        elif opt == 'path':     # path=<path to ballot file>
            path = arg
        elif opt == 'profile':  # profile=<number of repetitions>
            import cProfile
            import pstats
            reps = int(arg)
            doProfile = True
            profilefile = "profile.out"
    # else we pass the option along
    if not path:
        raise UsageError("no ballot file specfied")
    
    #  get the rule class
    #
    Rule = packages.rules.electionRule(rule)
    if not Rule:
        rules = ' '.join(packages.rules.electionRuleNames)
        raise UsageError("unknown rule %s; known rules:\n\t%s" % (rule, rules))

    #  run the election
    #
    #    fetch the election profile
    #    create the Election object
    #    count
    #    report
    #
    def countElection(repeat=1):
        "encapsulate for optional profiling"
        global E
        for i in xrange(repeat):
            E = Election(Rule, electionProfile, options=options)
            E.count()

    electionProfile = ElectionProfile(path=path)
    try:
        intr = False
        if doProfile:
            cProfile.runctx('countElection(reps)', globals(), locals(), profilefile)
        else:
            countElection(reps)
    except KeyboardInterrupt:
        intr = True
    global E  # if E isn't global, the profiled assignment of E isn't visible
    report = E.report(intr)
    if 'dump' in options:
        report += E.dump()

    if doProfile:
        p = pstats.Stats(profilefile)
        p.strip_dirs().sort_stats('time').print_stats(50)

    return report

#   provide a basic CLI
#
#   options appear on the command line in the form of opt=val
#   a single bare opt (no '=') is interpreted as a path to the ballot file
#   two bare opts are interpreted as a rule followed by the ballot file path
#
def usage(subject=None):
    "return a usage string"
    u = ''
    if subject:
        u = 'usage(%s)' % subject
    else:
        u = 'usage'
    return u
    
if __name__ == "__main__":
    options = dict()
    if len(sys.argv) < 2:
        print >>sys.stderr, usage()
        sys.exit(1)
    if len(sys.argv) > 1 and sys.argv[1] == 'help':
        if len(sys.argv) > 2:
            print usage(sys.argv[2])
        else:
            print usage()
        sys.exit(0)
    path = None
    try:
        for arg in sys.argv[1:]:
            optarg = arg.split('=')
            if len(optarg) == 1:
                if optarg[0] in packages.values.arithmeticClassNames:
                    options['arithmetic'] = optarg[0]
                elif optarg[0] in packages.rules.electionRuleNames:
                    options['rule'] = optarg[1]
                elif optarg[0] == 'dump':
                    options['dump'] = True
                else:
                    if path:
                        raise UsageError("multiple ballot files: %s and %s" % (path, optarg[0]))
                    path = optarg[0]
                    options['path'] = path
            else:
                options[optarg[0]] = optarg[1]
        if path is None:
            print >>sys.stderr, "droop: must specify ballot file"
            sys.exit(1)
        try:
            report = main(options)
        except ElectionProfile.ElectionProfileError as err:
            print >>sys.stderr, "** droop: Election profile error: %s" % err
            sys.exit(1)
        except packages.values.arithmeticValuesError as err:
            print >>sys.stderr, "** droop: %s" % err
            sys.exit(1)
        except Election.ElectionError as err:
            print >>sys.stderr, "** droop: Election error: %s" % err
            sys.exit(1)
    except UsageError as err:
        print >>sys.stderr, "** droop: %s" % err
        print >>sys.stderr, usage()
        sys.exit(1)
    print report
    sys.exit(0)