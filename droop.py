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


def main(options=None):
    "run an election"
    
    myname = 'droop'

    if not options:
        print >>sys.stderr, "%s: no ballot file" % myname
        sys.exit(1)
        
    rule = 'meek'  # default rule
    path = None    # ballot path must be specified
    
    for opt,arg in options.items():
        if opt == 'rule':
            rule = arg
        elif opt == 'path':
            path = arg
    # else we pass the option along
    if not path:
        print >> sys.stderr, "%s: no ballot file specfied" % myname
        sys.exit(1)
    
    if rule in packages.rules.electionRuleNames:
        Rule = packages.rules.electionRules[rule]
    else:
        print >> sys.stderr, "%s: unknown rule %s" % (myname, rule)
        print >> sys.stderr, "    known rules: %s" % ','.join(packages.rules.electionRuleNames)
        sys.exit(1)
    try:
        electionProfile = ElectionProfile(path=path)
    except ElectionProfile.ElectionProfileError as err:
        print >>sys.stderr, "**Election profile error: %s" % str(err)
        sys.exit(2)
    try:
        intr = False
        E = Election(Rule, electionProfile, options=options)
        E.count()
    except KeyboardInterrupt:
        intr = True
    report = E.report(intr)
    if 'dump' in options and options['dump']:
        report += E.dump()
    return report

#   provide a basic CLI
#
if __name__ == "__main__":
    rule = None
    path = None
    options = dict()
    for arg in sys.argv[1:]:
        optarg = arg.split('=')
        if len(optarg) == 1:
            rule = path
            path = optarg[0]
        else:
            options[optarg[0]] = optarg[1]
    if path is None:
        print >>sys.stderr, "droop: must specify ballot file"
        sys.exit(1)
    options['path'] = path
    if rule:
        options['rule'] = rule
    options['dump'] = True
    report = main(options)
    print report
    sys.exit(0)