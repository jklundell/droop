# -*- coding: utf-8 -*-
'''
Generic Election Support

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

Top-level structure:

  A driver program (for example Droop.py, the CLI) 
    1. creates an ElectionProfile from a ballot file,
    2. imports a Rule, 
    3. creates an Election(Rule, ElectionProfile, options),
    4. counts the election with Election.count(), and
    5. generates a report with Election.report().
  
  The options are used to override default Rule parameters, such as arithmetic.
'''

import sys, re, copy
import values
import droop
from droop.common import ElectionError, parseOptions

class Election(object):
    '''
    container for an election
    '''
    
    def __init__(self, electionProfile, options=dict()):
        "create an election from the incoming election profile"

        #  before this, a rule has been specified and a profile created
        #
        #  sequence of operations:
        #
        #    merge options from profile
        #    find rule class
        #    convert numeric option values to ints
        #    let rule process options (set defaults, etc)
        #    initialize arithmetic class
        #    save profile
        #    build candidate objects
        #    make a tiebreaking-order, if specified
        #    make the ballots object
        #
        if not electionProfile:
            raise ElectionError('no election profile specified')

        for opt, value in parseOptions(electionProfile.options).items():
            if opt not in options:
                options[opt] = value

        rulename = options.get('rule')
        if rulename is None:
            raise ElectionError('no election rule specified')
        Rule = droop.electionRule(rulename)    # get rule class
        if Rule is None:
            raise ElectionError('unknown election rule: %s' % rulename)
        self.rule = Rule(self)

        # convert numeric options (precision, etc) to ints
        for key, value in options.iteritems():
            if isinstance(value, str) and re.match(r'\d+$', value):
                options[key] = int(value)
        self.options_all = set(options)
        self.options_used = set(('rule', 'arithmetic'))
        self.options_ignored = set()
        self.options = self.rule.options(options, self.options_used, self.options_ignored)     # allow rule to process options
        self.V = values.ArithmeticClass(self.options, self.options_used, self.options_ignored) # then set arithmetic
        self.V0 = self.V(0)  # constant zero for efficiency
        self.V1 = self.V(1)  # constant one for efficiency
        self.electionProfile = electionProfile
        self.erecord = self.ElectionRecord(self)
        self.round = 0  # round number
        self.rounds = list()    # list of rounds for weak tiebreaking
        self.intr_logged = False

        #  create candidate objects for candidates in election profile
        #
        self.C = Candidates(self)
        for cid in sorted(electionProfile.eligible | electionProfile.withdrawn):
            c = Candidate(self, cid, electionProfile.candidateOrder[cid], 
                electionProfile.tieOrder[cid],
                electionProfile.candidateName[cid],
                electionProfile.nickName[cid],
                cid in electionProfile.withdrawn)
            self.C.add(c)

        #  create a ballot object (ranking candidate IDs) from the profile rankings of candidate IDs
        #  withdrawn candidates have been removed already
        #
        self.ballots = list()
        for bl in electionProfile.ballotLines:
            if bl.ranking:  # skip if only withdrawn candidates
                self.ballots.append(self.Ballot(self, bl.multiplier, bl.ranking))
        self.ballotsEqual = list()
        for bl in electionProfile.ballotLinesEqual:
            if bl.ranking:  # skip if only withdrawn candidates
                self.ballotsEqual.append(self.Ballot(self, bl.multiplier, bl.ranking))

    def count(self):
        "count the election"
        self.quota = self.V0
        self.surplus = self.V0
        self.votes = self.V0
        if self.rule.method == 'meek':
            self.residual = self.V0
        for c in self.C:
            c.vote = self.V0
        self.rule.count()   ### count the election ###
        self.logAction('end', 'Count Complete')
        self.elected = self.C.elected()
        self.defeated = self.C.defeated()
        self.withdrawn = self.C.withdrawn()

    def logAction(self, action, msg):
        "record an action"
        self.erecord.action(action, msg)

    def log(self, msg):
        "log a message as an action"
        self.logAction('log', msg)

    def newRound(self):
        "add a round"
        self.round += 1
        self.logAction('round', 'New Round')

    @classmethod
    def makehelp(cls):
        "build a dictionary of help strings on various subjects"
        helps = dict()
        helps['rule'] =  'available rules: %s' % ','.join(droop.electionRuleNames())
        for name in droop.electionRuleNames():
            droop.ruleByName[name].helps(helps, name)
        values.helps(helps)
        return helps

    @property
    def title(self):
        "election title"
        return self.electionProfile.title

    @property
    def nSeats(self):
        "number of seats"
        return self.electionProfile.nSeats
        
    @property
    def nBallots(self):
        "number of ballots"
        return self.electionProfile.nBallots
        
    def candidate(self, cid):
        "look up a candidate from a candidate ID"
        return self.C.byCid(cid)
        
    def prog(self, msg):
        "log to the console (immediate output)"
        sys.stdout.write(msg)
        sys.stdout.flush()

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - len(self.C.elected())

    def record(self):
        "return the election record as a dict"
        return dict(self.erecord)

    def report(self, intr=False):
        "return the election record as a formatted report"
        if intr and not self.intr_logged:
            self.log('** count interrupted; this round is incomplete **')
            self.intr_logged = True
        return self.erecord.report(intr)

    def dump(self, intr=False):
        "return the election record as tab-separated fields"
        if intr and not self.intr_logged:
            self.log('** count interrupted; this round is incomplete **')
            self.intr_logged = True
        return self.erecord.dump()

    def json(self, intr=False):
        "return the election record as a JSON string"
        if intr and not self.intr_logged:
            self.log('** count interrupted; this round is incomplete **')
            self.intr_logged = True
        return self.erecord.json()

    class ElectionRecord(dict):
        "complete record of an election"
        
        def __init__(self, E):
            "create the base of the election record"
            self.E = E
            self.filled = False
            self['actions'] = list()    # list of election actions

        def fill(self):
            "fill in the basic election info"
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
            self['cids'] = E.C.cidList("all")       # all CIDs
            self['ecids'] = E.C.cidList("eligible") # eligible CIDs
            self['cdict'] = E.C.cDict()
            ignored = list()
            for opt in E.options_all:
                if opt in E.options_ignored or opt not in E.options_used:
                    ignored.append(opt)
            if ignored:
                self['options_ignored'] = sorted(ignored)
            self['options_used'] = sorted(E.options_used)
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
            if tag == "log":
                self['actions'].append(A)
                return
            if (tag == "begin" or tag == "round") and not self.filled:
                self.fill()
            if tag == "end":
                vreport = E.V.report()
                if vreport:
                    self['arithmetic_report'] = vreport
            if tag == "round":
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
            elif self['method'] == 'qpq':
                A['votes'] = E.votes    # total votes
            self['actions'].append(A)

        def report(self, intr=False):
            "report an action"
            E = self.E
            V = E.V
            s = "\nElection: %s\n\n" % self['title']
            s += "\tDroop package: %s v%s\n" % (self['droop_name'], self['droop_version'])
            s += "\tRule: %s\n" % self['rule_info']
            s += "\tArithmetic: %s\n" % self['arithmetic_info']
            if self.get('options_ignored') is not None:
                s += "\tIgnored options: %s\n" % ", ".join(self.get('options_ignored'))
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
            if intr:    # pragma: no cover
                s += "\t** Count terminated prematurely by user interrupt **\n\n"
            if self.get('arithmetic_report') is not None:
                s += self.get('arithmetic_report')
            cids = self['cids']
            cdict = self['cdict']
            report = [s]
            ra = E.rule.reportActions(self) # allow rule to override default report of actions
            if ra is not None:
                return "".join(report, ra)
            for A in self['actions']:
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
                    if self['method'] == 'qpq':
                        for cid in ecids:
                            s += '\tElected:  %s (%s)\n' % (cdict[cid]['name'], V(cstate[cid]['quotient']))
                        for cid in hcids:
                            s += '\tHopeful:  %s (%s)\n' % (cdict[cid]['name'], V(cstate[cid]['quotient']))
                        for cid in dcids:
                            s += '\tDefeated: %s (%s)\n' % (cdict[cid]['name'], V(cstate[cid]['quotient']))
                    else:
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
                elif self['method'] == 'qpq':
                    s += '\tQuota: %s\n' % V(A['quota'])
                report.append(s)
            return "".join(report)
            
        def dump(self):
            "dump a list of actions"

            V = self.E.V
            ecids = self['ecids']
            cdict = self['cdict']
            
            #  header line
            #
            h = ['R', 'Action', 'Quota']
            if self['method'] == 'meek':
                h += ['Votes', 'Surplus', 'Residual']
            elif self['method'] == 'wigm':
                h += ['Total', 'Votes', 'Non-Transferable', 'Residual']
            elif self['method'] == 'qpq':
                pass

            for cid in ecids:
                h += ['%s.name' % cid]
                h += ['%s.state' % cid]
                if self['method'] == 'qpq':
                    h += ['%s.quotient' % cid]
                else:
                    h += ['%s.vote' % cid]
                if self['method'] == 'meek': h += ['%s.kf' % cid]
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
                    if self['method'] == 'meek':
                        r += [V(A['votes']), V(A['surplus']), V(A['residual'])]
                    elif self['method'] == 'wigm':
                        votes = A['e_votes'] + A['p_votes'] + A['h_votes'] + A['d_votes']
                        total = votes + A['nt_votes'] + A['residual']
                        r += [V(total), V(votes), V(A['nt_votes']), V(A['residual'])]
                    elif self['method'] == 'qpq':
                        pass
    
                    for cid in ecids:
                        cstate = A['cstate'][cid]
                        r.append(cdict[cid]['name'])
                        r.append(cstate['code'])
                        if self['method'] == 'qpq':
                            r.append(V(cstate['quotient']))
                        else:
                            r.append(V(cstate['vote']))
                        if self['method'] == 'meek': r.append(V(cstate['kf']))
    
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

    class Ballot(object):
        '''
        internal representation of one ballot
        
        The use of slots gives a more compact object, which significantly
        reduces memory requirements for large elections.
        
        Similarly, ranking, from the election profile, is an array
        of bytes or shorts (depending on candidate count), again
        for memory efficiency.
        
        The ballot multiplier comes from the election profile, and is
        a count of identical ballots.
        
        The ballot weight, initially 1, is the ballot's current weight
        after possible reduction via surplus transfers.
        '''
        
        __slots__ = ('E', 'multiplier', 'index', 'weight', 'residual', 'ranking')
        
        def __init__(self, E, multiplier=1, ranking=None):
            "create a ballot"
            self.E = E
            self.multiplier = E.V(multiplier)  # number of ballots like this
            self.index = 0                # current ranking
            self.weight = E.V1            # initial weight
            self.residual = E.V0          # untransferable weight
            self.ranking = ranking

        def advance(self):
            "advance ballot index to next-ranked candidate"
            self.index += 1

        def restart(self, weight):
            "restart a ballot (for qpq)"
            self.index = 0
            self.weight = weight
            self.residual = self.E.V0

        @property
        def exhausted(self):
            "is ballot exhausted?"
            return self.index >= len(self.ranking)    # detect end-of-ranking
        
        @property
        def topRank(self):
            "return top rank (CID or tuple), or None if exhausted"
            return self.ranking[self.index] if self.index < len(self.ranking) else None
        
        @property
        def topCand(self):
            "return top candidate, or None if exhausted"
            return self.E.C.byCid(self.ranking[self.index]) if self.index < len(self.ranking) else None
        
        @property
        def vote(self):
            "return total vote of this ballot"
            if self.multiplier == self.E.V1:
                return self.weight  # faster
            return self.weight * self.multiplier
            

class Candidates(set):
    '''
    all candidates
    '''
    def __init__(self, E=None):
        "new Candidates"
        self.E = E              # Election
        self._byCid = dict()    # side table: cid -> Candidate

    def copy(self):
        "return a copy of ourself"
        C = Candidates(self.E)
        for c in self:
            super(Candidates, C).add(copy.copy(c))
        return C

    def add(self, c):
        "add a candidate"
        self._byCid[c.cid] = c  # side table for lookup by candidate ID
        super(Candidates, self).add(c)
        if self.E is not None:  # accommodate unit test
            if c.state == "withdrawn":
                self.E.log("Add withdrawn: %s" % c.name)
            else:
                self.E.log("Add eligible: %s" % c.name)

    def byCid(self, cid):
        "look up a candidate by candidate ID"
        return self._byCid[cid]

    def cidList(self, state="all"):
        '''
        return a list of CIDs, in ballot order
        
        used for reporting
        '''
        return [c.cid for c in self.select(state, order="ballot")]

    def cDict(self):
        '''
        return dict of candidate static info, keyed by CID
        variant state is not included (see cState())
        
        used for reporting
        '''
        cdict = dict()
        for c in self.select("all"):
            cdict[c.cid] = c.as_dict(ro=True)
        return cdict

    def cState(self):
        '''
        return a dict of candidate state, keyed by CID
        invariant state is not included (see cDict())
        withdrawn candidates have an abbreviated state (see c.as_dict())
        
        used for reporting
        '''
        cstate = dict()
        for c in self.select("all"):
            cstate[c.cid] = c.as_dict(rw=True)
        return cstate

    @staticmethod
    def byBallotOrder(candidates, reverse=False):
        "sort a list of candidates by ballot order"
        return sorted(candidates, key=lambda c: c.order, reverse=reverse)

    @staticmethod
    def byVote(candidates, reverse=False):
        "sort a list of candidates by vote order"
        return sorted(candidates, key=lambda c: (c.vote, c.order), reverse=reverse)

    @staticmethod
    def byTieOrder(candidates, reverse=False):
        "sort a list of candidates by tie-break order"
        return sorted(candidates, key=lambda c: c.tieOrder, reverse=reverse)

    def select(self, state, order="none", reverse=False):
        "select and return list of candidates with specified state, optionally in specified order"
        if state == "all":
            candidates = self
        elif state == "eligible":
            candidates = [c for c in self if c.state != "withdrawn"]
        elif state == "pending":
            candidates = [c for c in self if c.state == "elected" and c.pending]
        elif state == "notpending":
            candidates = [c for c in self if c.state == "elected" and not c.pending]
        else:
            candidates = [c for c in self if c.state == state]
        if order == "none":
            return candidates
        if order == "ballot":
            return self.byBallotOrder(candidates, reverse=reverse)
        if order == "tie":
            return self.byTieOrder(candidates, reverse=reverse)
        if order == "vote":
            return self.byVote(candidates, reverse=reverse)
        raise ValueError('unknown candidate sort order: %s' % order)

    def eligible(self, order="none", reverse=False):
        "select and return list of eligible candidates, in specified order"
        return self.select("eligible", order, reverse)

    def withdrawn(self, order="none", reverse=False):
        "select and return list of eligible candidates, in specified order"
        return self.select("withdrawn", order, reverse)

    def hopeful(self, order="none", reverse=False):
        "select and return list of hopeful candidates, in specified order"
        return self.select("hopeful", order, reverse)

    def elected(self, order="none", reverse=False):
        "select and return list of withdrawn candidates, in specified order"
        return self.select("elected", order, reverse)

    def defeated(self, order="none", reverse=False):
        "select and return list of defeated candidates, in specified order"
        return self.select("defeated", order, reverse)

    def notpending(self, order="none", reverse=False):
        "select and return list of elected and not pending candidates, in specified order"
        return self.select("notpending", order, reverse)

    def pending(self, order="none", reverse=False):
        "select and return list of elected candidates pending transfer, in specified order"
        return self.select("pending", order, reverse)


class Candidate(object):
    '''
    a candidate, with state
    '''
    def __init__(self, E, cid, ballotOrder, tieOrder, cname, cnick, isWithdrawn):
        "new candidate"
        # immutable properties
        self.E = E
        self.cid = cid              # candidate id
        self.order = ballotOrder    # ballot order
        self.tieOrder = tieOrder    # tie-breaking order
        self.name = cname           # candidate name
        self.nick = str(cid) if cnick is None else str(cnick)
        # mutable properties
        self.state = "withdrawn" if isWithdrawn else "hopeful"  # withdrawn, hopeful, elected, etc
        if E is None:
            self.vote = None        # in support of unit tests
        else:
            self.vote = E.V0        # current vote total
        self.kf = None              # current keep factor (meek)
        self.quotient = None        # current quotient (qpq)
        self.pending = None         # surplus-transfer pending (wigm)

    def as_dict(self, ro=False, rw=False):
        "return as a dict suitable for JSON encoding"
        cdict = dict()
        if ro:
            cdict['cid'] = self.cid
            cdict['ballot_order'] = self.order
            cdict['tie_order'] = self.tieOrder
            cdict['name'] = self.name
            cdict['nick'] = self.nick
        if rw:
            cdict['state'] = self.state
            cdict['code'] = self.code()
            if self.state != 'withdrawn':
                cdict['vote'] = self.vote
                if self.kf is not None:
                    cdict['kf'] = self.kf
                if self.quotient is not None:
                    cdict['quotient'] = self.quotient
                if self.pending is not None:
                    cdict['pending'] = self.pending
        return cdict

    @property
    def surplus(self):
        "return candidate's current surplus vote"
        s = self.vote - self.E.quota
        return self.E.V0 if s < self.E.V0 else s
        
    def elect(self, msg='Elect'):
        '''
        Meek, QPQ: elect a candidate
        WIGM: move a candidate from pending to elected on surplus transfer
        '''
        self.state = "elected"
        self.pending = False
        self.E.logAction('elect', "%s: %s" % (msg, self.name))

    def pend(self, msg='Elect, transfer pending'):
        '''
        WIGM: set a candidate elected pending transfer
        '''
        self.state = "elected"
        self.pending = True
        self.E.logAction('pend', "%s: %s" % (msg, self.name))

    def unelect(self):
        "QPQ: unelect a candidate (qpq restart)"
        self.state = "hopeful"

    def defeat(self, msg='Defeat'):
        "defeat a candidate"
        self.state = "defeated"
        self.E.logAction('defeat', "%s: %s" % (msg, self.name))

    def code(self):
        "return a one-letter state code for a candidate"
        if self.state == "withdrawn": return 'W'
        if self.state == "hopeful": return 'H'
        if self.state == "elected":
            if self.E.rule.method == 'wigm' and self.pending: return 'e'
            return 'E'
        if self.state == "defeated": return 'D'
        return '?'  # pragma: no cover

    def __str__(self):
        "use candidate name as the string representation"
        return self.name

    def __hash__(self):
        "use candidate id as the candidate hash"
        return self.cid

    def __eq__(self, other):
        "test for equality of cid"
        if isinstance(other, int):
            return self.cid == other
        if isinstance(other, str):
            return str(self.cid) == other
        if other is None:
            return False
        return self.cid == other.cid
