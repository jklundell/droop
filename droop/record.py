# -*- coding: utf-8 -*-
'''
droop: election record support

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

from __future__ import absolute_import
from . import common
from . import values

class ElectionRecord(dict):
    "complete record of an election"
    
    def __init__(self, E):
        "create the base of the election record"
        super(ElectionRecord, self).__init__()
        self.E = E
        self.filled = False
        self['actions'] = list()    # list of election actions

    def _fill(self):
        """
        fill in the basic election info
        """
        E = self.E
        self['title'] = E.title
        self['droop_name'] = common.droopName
        self['droop_version'] = common.droopVersion
        self['rule_name'] = E.rule.name
        self['rule_info'] = E.rule.info()
        self['method'] = E.rule.method
        self['arithmetic_name'] = E.V.name
        self['arithmetic_info'] = E.V.info
        self['seats'] = E.nSeats
        self['nballots'] = E.nBallots
        self['quota'] = E.quota
        self['cids'] = E.C.cidList('all')       # all CIDs
        self['ecids'] = E.C.cidList('eligible') # eligible CIDs
        self['cdict'] = E.C.cDict()             # candidate descriptors
        self['options'] = E.options.record()    # all options
        if hasattr(E.rule, 'omega'):
            self['omega'] = E.rule.omega
        if E.electionProfile.source:
            self['profile_source'] = E.electionProfile.source
        if E.electionProfile.comment:
            self['profile_comment'] = E.electionProfile.comment
        E.rule.action(self, None)               # give rule a chance
        self.filled = True

    def action(self, tag, msg):
        "add an action to the election report"
        assert(tag in (
            'begin',    # beginning of count
            'log',      # log an arbitrary string
            'round',    # start a new round
            'tie',      # break a tie
            'elect',    # elect a candidate
            'defeat',   # defeat a candidate
            'iterate',  # terminate an iteration (meek)
            'unpend',   # set pending false (wigm)
            'transfer', # transfer a surplus (wigm)
            'end'       # end of count
            ))
        E = self.E
        C = E.C
        A = dict(tag=tag, msg=msg, round=E.round)
        if tag == 'log':
            self['actions'].append(A)
            return
        if (tag == 'begin' or tag == 'round') and not self.filled:
            self._fill()
        if tag == 'end':
            vreport = E.V.report()
            if vreport:
                self['arithmetic_report'] = vreport
        if tag == 'round':
            E.rounds.append(C.copy())    # save a copy of the Candidates state for weak tiebreaking
        A['cstate'] = C.cState()  # variable candidate state
        A['votes'] = sum([c.vote for c in C.eligible()], E.V0)
        A['quota'] = E.quota
        E.rule.action(self, A)                  # give rule a chance at the action
        self['actions'].append(A)

    def report(self, intr=False):
        "report an action"
        E = self.E
        report = []
        if E.rule.report(self, report, 'all'):  # allow rule to supply entire report
            return "".join(report)
        
        #  report header
        #
        if not E.rule.report(self, report, 'header'):   # allow rule to supply report header
            s = "\nElection: %s\n\n" % self['title']
            s += "\tDroop package: %s v%s\n" % (self['droop_name'], self['droop_version'])
            s += "\tRule: %s\n" % self['rule_info']
            s += "\tArithmetic: %s\n" % self['arithmetic_info']
            unused = E.options.unused()
            if unused:
                s += "\tUnused options: %s\n" % ", ".join(unused)
            overrides = E.options.overrides()
            if overrides:
                s += "\tOverridden options: %s\n" % ", ".join(overrides)
            s += "\tSeats: %d\n" % self['seats']
            s += "\tBallots: %d\n" % self['nballots']
            s += "\tQuota: %s\n" % self['quota']
            report.append(s)
            
            #  allow rule to append to header
            #
            E.rule.report(self, report, 'headerappend')
            
            #  include profile source & comment from ballot file
            #
            if self.get('profile_source') is not None:
                report.append("Source: %s\n" % self.get('profile_source'))
            if self.get('profile_comment') is not None:
                report.append("{%s}\n" % self.get('profile_comment'))
            report.append("\n")

        #  report arithmetic
        #
        if self.get('arithmetic_report') is not None:
            report.append(self.get('arithmetic_report'))
        
        #  report interrupted count
        #
        if intr:
            report.append("\t** Count terminated prematurely by user interrupt **\n\n")
        
        #  report actions
        #
        if not E.rule.report(self, report, 'actions'):          # allow rule to report all actions
            cids = self['cids']
            cdict = self['cdict']
            for A in self['actions']:
                if E.rule.report(self, report, 'action', A):    # allow rule to report this action
                    continue
                if A['tag'] == 'log':
                    report.append("\t%s\n" % A['msg'])
                    continue
                if A['tag'] == 'round':
                    report.append("Round %d:\n" % A['round'])
                    continue
                cstate = A['cstate']
                ecids = [cid for cid in cids if cstate[cid]['state'] == 'elected']
                hcids = [cid for cid in cids if cstate[cid]['state'] == 'hopeful']
                dcids = [cid for cid in cids if cstate[cid]['state'] == 'defeated']
                s = 'Action: %s\n' % (A['msg'])
                if A['tag'] in ('begin', 'elect', 'defeat', 'pend', 'transfer', 'end'):
                    for cid in [cid for cid in ecids if not cstate[cid].get('pending')]:
                        s += '\tElected:  %s (%s)\n' % (cdict[cid]['name'], cstate[cid]['vote'])
                    for cid in [cid for cid in ecids if cstate[cid].get('pending')]:
                        s += '\tPending:  %s (%s)\n' % (cdict[cid]['name'], cstate[cid]['vote'])
                    for cid in hcids:
                        s += '\tHopeful:  %s (%s)\n' % (cdict[cid]['name'], cstate[cid]['vote'])
                    for cid in [cid for cid in dcids if cstate[cid]['vote'] > E.V0]:
                        s += '\tDefeated: %s (%s)\n' % (cdict[cid]['name'], cstate[cid]['vote'])
                    c0 = [cdict[cid]['name'] for cid in dcids if cstate[cid]['vote'] == E.V0]
                    if c0:
                        s += '\tDefeated: %s (%s)\n' % (', '.join(c0), E.V0)
                report.append(s)
                
                #  allow rule to append to this action
                #
                E.rule.report(self, report, 'actionappend', A)    # allow rule to append to this action

        return "".join(report)
        
    def dump(self):
        "dump a list of actions"

        E = self.E
        ecids = self['ecids']
        cdict = self['cdict']
        
        #  header line
        #
        h = ['R', 'Action', 'Quota']
        E.rule.dump(h)

        for cid in ecids:
            h += ['%s.name' % cid]
            h += ['%s.state' % cid]
            E.rule.dump(h, cid=cid)
        h = [str(item) for item in h]

        dumps = ['\t'.join(h) + '\n']
        cdict = self['cdict']
        for A in self['actions']:
            #  dump a line of data
            #
            if A['tag'] in ('round', 'log', 'iterate'):
                r = [A['round'], A['tag'], A['msg']]
            else:
                rnd = 'X' if A['tag'] == 'end' else A['round']
                r = [rnd, A['tag'], A['quota']]
                E.rule.dump(r, action=A)

                for cid in ecids:
                    cstate = A['cstate'][cid]
                    r.append(cdict[cid]['name'])
                    r.append(cstate['code'])
                    E.rule.dump(r, action=A, cid=cid, cstate=cstate)

            r = [str(item) for item in r]
            dumps.append('\t'.join(r) + '\n')
        return "".join(dumps)

    def json(self):
        "dump election history as a JSON-encoded string"
        import json as json_
        from fractions import Fraction

        class ValueEncoder(json_.JSONEncoder):
            "provide JSON encoding for droop arithmetic object"
            def default(self, obj): # pylint: disable=E0202
                "handle Rational objects that escape to Fraction"
                if isinstance(obj, Fraction):
                    return str(values.rational.Rational(obj))
                if isinstance(obj, (values.fixed.Fixed, values.guarded.Guarded, values.rational.Rational)):
                    return str(obj)
                return json_.JSONEncoder.default(self, obj) # pragma: no cover

        return json_.dumps(self, cls=ValueEncoder, sort_keys=True, indent=2)
