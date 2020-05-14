#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Droop external interface

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


   main(options)

   main is a convenience function for running an election from outside

   options is a dictionary that must, at a minimum, include a path to a ballot file
   It may also include rule parameters and report requests (pending)

   The default rule is 'meek'

   options currently include:
   path=ballot_file_path
   rule=election_rule_name
     omega=<set meek surplus limit to 10^-epsilon>
   report= [not currently supported]
   arithmetic=guarded|fixed|integer|rational
     (integer is fixed with precision=0)
     precision=<precision for fixed or guarded, in digits>
     guard=<guard for guarded, in digits>
     dp=<display precision (digits) for rational>
'''

import sys
import os
import cProfile
import pstats
import droop
from droop.profile import ElectionProfile, ElectionProfileError
from droop.election import Election

def main(options=None):
    "run an election"

    if not options:
        raise droop.common.UsageError("no ballot file specified")

    #  process options
    #
    #  we know about (path, profile)
    #  all the others are passed to the various consumers
    #
    path = None         # ballot path must be specified
    doProfile = False   # performance profiling
    reps = 1            # repetitions (for profiling)
    for opt, arg in list(options.items()):
        if opt == 'path':     # path=<path to ballot file>
            path = arg
        elif opt == 'profile':  # profile=<number of repetitions>
            reps = int(arg)
            doProfile = True
            profilefile = "profile.out"
    if not path:
        raise droop.common.UsageError("no ballot file specfied")

    #  run the election
    #
    #    fetch the election profile
    #    create the Election object
    #    count
    #    report
    #
    def countElection(E, repeat=1):
        "encapsulate for optional profiling"
        for _ in range(repeat):
            E.count()

    electionProfile = ElectionProfile(path=path)  # don't repeat the profile loading
    E = Election(electionProfile, options)
    try:
        intr = False
        if doProfile:
            cProfile.runctx('countElection(E, reps)', globals(), locals(), profilefile)
        else:
            countElection(E, reps)
    except KeyboardInterrupt:
        intr = True
    E.options.setopt('dump', default=False)
    E.options.setopt('json', default=False)
    ereport = ''
    if E.options.setopt('report', default=True):
        ereport += E.report(intr)
    if E.options.getopt('dump'):
        ereport += E.dump(intr)
    if E.options.getopt('json'):
        ereport += E.json(intr)

    if doProfile:
        p = pstats.Stats(profilefile)
        p.strip_dirs().sort_stats('time').print_stats(50)

    return ereport

#   provide a basic CLI
#
#   options appear on the command line in the form of opt=val
#   a single bare opt (no '=') is interpreted as a path to the ballot file
#   two bare opts are interpreted as a rule followed by the ballot file path
#
me = os.path.basename(__file__)

def usage(subject=None):
    "usage and help"

    helps = Election.makehelp()
    helpers = sorted(helps.keys())

    u = '\n%s v%s\n' % (droop.common.droopName, droop.common.droopVersion)
    u += '\nUsage:\n'
    u += '%s options ballotfile\n' % me
    u += '  options:\n'
    u += '    rule name (%s)\n' % ','.join(droop.electionRuleNames())
    u += '    arithmetic class name (%s)\n' % ','.join(droop.values.arithmeticNames)
    u += '    profile=reps, to profile the count, running reps repetitions\n'
    u += '    dump, to dump a csv of the election actions\n'
    u += '    rule- or arithmetic-specific options:\n'
    u += '      precision=n: decimal digits of precision (fixed, guarded)\n'
    u += '      guard=n: guard digits (guarded; default to guard=precision)\n'
    u += '      dp=n: display precision (rational)\n'
    u += '      omega=n: meek iteration terminates when surplus < 1/10^omega\n'
    u += '\n'
    u += '  help is available on the following subjects:\n'
    u += '    %s' % ' '.join(helpers)
    helps['usage'] = u

    if not subject:
        return u
    if subject in helps:
        return '\n%s' % helps[subject]
    return 'no help available on %s' % subject


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(usage(), file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) > 1 and sys.argv[1] == 'help':
        if len(sys.argv) > 2:
            print(usage(sys.argv[2]))
        else:
            print(usage())
        sys.exit(0)
    ballotpath = None
    try:
        eoptions = droop.options.Options.parse(sys.argv[1:])
        ballotpath = eoptions.get('path')
        if ballotpath is None:
            print("droop: must specify ballot file", file=sys.stderr)
            sys.exit(1)
        try:
            report = main(eoptions)
        except ElectionProfileError as err:
            print("** droop: Election profile error: %s" % err, file=sys.stderr)
            sys.exit(1)
        except droop.values.ArithmeticValuesError as err:
            print("** droop: %s" % err, file=sys.stderr)
            sys.exit(1)
        except droop.common.ElectionError as err:
            print("** droop: Election error: %s" % err, file=sys.stderr)
            sys.exit(1)
    except droop.common.UsageError as err:
        print("** droop: %s" % err, file=sys.stderr)
        print(usage(), file=sys.stderr)
        sys.exit(1)
    print(report)
    sys.exit(0)
