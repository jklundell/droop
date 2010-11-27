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

import values
import droop

class ElectionRecord(dict):
    "complete record of an election"
    
    def __init__(self, E):
        "create the base of the election record"
        self.E = E
        self.filled = False
        self['actions'] = list()    # list of election actions

    def _fill(self):
        """
        fill in the basic election info
        """
        E = self.E
        self['title'] = E.title
        self['droop_name'] = droop.common.droopName
        self['droop_version'] = droop.common.droopVersion
        self['rule_name'] = E.rule.name
        self['rule_info'] = E.rule.info()
        self['method'] = E.rule.method
        self['arithmetic_name'] = E.V.name
        self['arithmetic_info'] = E.V.info
        self['seats'] = E.nSeats
        self['nballots'] = E.nBallots
        self['quota'] = E.V(E.quota)
        self['cids'] = E.C.cidList('all')       # all CIDs
        self['ecids'] = E.C.cidList('eligible') # eligible CIDs
        self['cdict'] = E.C.cDict()             # candidate descriptors
        self['options'] = E.options.record()    # all options
        if self['method'] == 'meek':
            self['omega'] = E.rule._omega
        if E.electionProfile.source:
            self['profile_source'] = E.electionProfile.source
        if E.electionProfile.comment:
            self['profile_comment'] = E.electionProfile.comment
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
            'pend',     # elect a candidate pending surplus transfer (wigm)
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
        if self['method'] == 'meek':
            A['residual'] = E.residual  # meek residual is the nontransferable portion
            A['surplus'] = E.V(E.surplus)
        elif self['method'] == 'wigm':
            #
            #  this is expensive in a big election, so we've done a little optimization
            #
            A['nt_votes'] = sum((b.vote for b in E.ballots if b.exhausted), E.V0) # nontransferable votes
            A['h_votes'] = sum((c.vote for c in C.hopeful()), E.V0)     # votes for hopeful candidates
            A['e_votes'] = sum((c.vote for c in C.notpending()), E.V0)  # votes for elected (transfer not pending) candidates
            A['p_votes'] = sum((c.vote for c in C.pending()), E.V0)     # votes for elected (transfer pending) candidates
            A['d_votes'] = sum((c.vote for c in C.defeated()), E.V0)    # votes for defeated candidates
            total = A['e_votes'] + A['p_votes'] + A['h_votes'] + A['d_votes'] + A['nt_votes']  # vote total
            A['residual'] = E.V(E.nBallots) - total                     # votes lost due to rounding error
            A['surplus'] = E.V(E.surplus)
        E.rule.action(self, A)                  # give rule a chance at the action
        self['actions'].append(A)

    def report(self, intr=False):
        "report an action"
        E = self.E
        V = E.V
        report = []
        if E.rule.report(self, report, 'all'):  # allow rule to supply entire report
            return "".join(report)
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
            s += "\tQuota: %s\n" % V(self['quota'])
            if self.get('omega') is not None:
                s += "\tOmega: %s\n" % self.get('omega')
            if self.get('profile_source') is not None:
                s += "Source: %s\n" % self.get('profile_source')
            if self.get('profile_comment') is not None:
                s += "{%s}\n" % self.get('profile_comment')
            s += '\n'
            report.append(s)
        E.rule.report(self, report, 'headerappend')     # allow rule to append to header
        if self.get('arithmetic_report') is not None:
            report.append(self.get('arithmetic_report'))
        if intr:
            s += "\t** Count terminated prematurely by user interrupt **\n\n"
        cids = self['cids']
        cdict = self['cdict']
        if not E.rule.report(self, report, 'actions'):          # allow rule to report all actions
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
                        s += '\tElected:  %s (%s)\n' % (cdict[cid]['name'], V(cstate[cid]['vote']))
                    for cid in [cid for cid in ecids if cstate[cid].get('pending')]:
                        s += '\tPending:  %s (%s)\n' % (cdict[cid]['name'], V(cstate[cid]['vote']))
                    for cid in hcids:
                        s += '\tHopeful:  %s (%s)\n' % (cdict[cid]['name'], V(cstate[cid]['vote']))
                    for cid in [cid for cid in dcids if cstate[cid]['vote'] > E.V0]:
                        s += '\tDefeated: %s (%s)\n' % (cdict[cid]['name'], V(cstate[cid]['vote']))
                    c0 = [cdict[cid]['name'] for cid in dcids if cstate[cid]['vote'] == E.V0]
                    if c0:
                        s += '\tDefeated: %s (%s)\n' % (', '.join(c0), E.V0)
                if self['method'] == 'meek':
                    s += '\tQuota: %s\n' % V(A['quota'])
                    s += '\tVotes: %s\n' % V(A['votes'])
                    s += '\tResidual: %s\n' % V(A['residual'])
                    s += '\tTotal: %s\n' % V((A['votes'] + A['residual']))
                    s += '\tSurplus: %s\n' % V(A['surplus'])
                elif self['method'] == 'wigm':
                    s += '\tElected votes: %s\n' % V(A['e_votes'])
                    if A['p_votes']:
                        s += '\tPending votes: %s\n' % V(A['p_votes'])
                    s += '\tHopeful votes: %s\n' % V(A['h_votes'])
                    if A['d_votes']:
                        s += '\tDefeated votes: %s\n' % V(A['d_votes'])
                    s += '\tNontransferable votes: %s\n' % V(A['nt_votes'])
                    s += '\tResidual: %s\n' % V(A['residual'])
                    s += '\tTotal: %s\n' % V(A['e_votes'] + A['p_votes'] + A['h_votes'] + A['d_votes'] + A['nt_votes'] + A['residual'])
                    s += '\tSurplus: %s\n' % V(A['surplus'])
                report.append(s)
        return "".join(report)
        
    def dump(self):
        "dump a list of actions"

        E = self.E
        V = E.V
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
                round = 'X' if A['tag'] == 'end' else A['round']
                r = [round, A['tag'], V(A['quota'])]
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
            def default(self, obj):
                "handle Rational objects that escape to Fraction"
                if isinstance(obj, Fraction):
                    return str(values.rational.Rational(obj))
                if isinstance(obj, (values.fixed.Fixed, values.guarded.Guarded, values.rational.Rational)):
                    return str(obj)
                return json_.JSONEncoder.default(self, obj) # pragma: no cover

        return json_.dumps(self, cls=ValueEncoder, sort_keys=True, indent=2)
