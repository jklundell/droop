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

import sys, re
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
        self.rule = Rule

        # convert numeric options (precision, etc) to ints
        for key, value in options.iteritems():
            if isinstance(value, str) and re.match(r'\d+$', value):
                options[key] = int(value)
        self.options = self.rule.options(options)     # allow rule to process options
        self.V = values.ArithmeticClass(self.options) # then set arithmetic
        self.V0 = self.V(0)  # constant zero for efficiency
        self.V1 = self.V(1)  # constant one for efficiency
        self.electionProfile = electionProfile

        #  create candidate objects for candidates in election profile
        #
        self.candidates = dict()  # cid: Candidate
        for cid in sorted(electionProfile.eligible | electionProfile.withdrawn):
            c = Candidate(self, cid, electionProfile.candidateOrder(cid), 
                electionProfile.tieOrder[cid],
                electionProfile.candidateName(cid),
                electionProfile.nickName[cid])
            self.candidates[cid] = c

        #  create a ballot object (ranking candidate IDs) from the profile rankings of candidate IDs
        #  withdrawn candidates have been removed alreay
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
        self.round = 0                    # round number
        self.rounds = []                  # per-round list of CandidateState for weak-tie-breaking
        self.actions = []                 # list of actions
        self.quota = self.V0
        self.surplus = self.V0
        self.votes = self.V0
        if self.rule.method() == 'meek':
            self.residual = self.V0
        elif self.rule.method() == 'qpq':
            self.ta = None
            self.tx = None
        self.CS = CandidateState(self)    # candidate state
        self.elected = CandidateSet()     # for communicating results
        self.eligible = CandidateSet()
        self.withdrawn = CandidateSet()
        for cid, c in self.candidates.iteritems():
            c.vote = self.V0
            self.CS.addCandidate(c, isWithdrawn=cid in self.electionProfile.withdrawn)
        self.rule.count(self)
        self.logAction('final', 'Count Complete')
        # TODO: end-of-election Action?
        self.elected = self.CS.elected

    def logAction(self, action, msg):
        "record an action"
        self.actions.append(self.Action(self, action, msg))

    def log(self, msg):
        "log a message as an action"
        self.logAction('log', msg)

    def newRound(self):
        "add a round"
        self.rounds.append(self.CS.copy())  # CandidateState for weak-tie-breaking
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
        return self.candidates[cid]
        
    def prog(self, msg):
        "log to the console (immediate output)"
        sys.stdout.write(msg)
        sys.stdout.flush()

    def signature(self):
        "return election signature (compact form of critical actions)"
        s = ''
        for action in self.actions:
            s += action.signature()
        return s

    def report(self, intr=False):
        "report election by round:action"
        s = "\nElection: %s\n\n" % self.title
        s += "\tDroop package: %s v%s\n" % (droop.common.droopName, droop.common.droopVersion)
        s += "\tRule: %s\n" % self.rule.info()
        s += "\tArithmetic: %s\n" % self.V.info
        s += "\tSeats: %d\n" % self.nSeats
        s += "\tBallots: %d\n" % self.nBallots
        s += "\tQuota: %s\n" % self.V(self.quota)
        if self.rule.method() == 'meek':
            s += "\tOmega: %s\n" % self.rule._omega
        if self.electionProfile.source:
            s += "Source: %s\n" % self.electionProfile.source
        if self.electionProfile.comment:
            s += "{%s}\n" % self.electionProfile.comment
        s += '\n'
        if intr:    # pragma: no cover
            s += "\t** Count terminated prematurely by user interrupt **\n\n"
            self.log('** count interrupted; this round is incomplete **')
        s += self.V.report()
        for action in self.actions:
            s += action.report()
        return s

    def dump(self):
        "dump election by action"
        s = self.actions[0].dump(header=True)
        for action in self.actions:
            s += action.dump()
        return s

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - len(self.CS.elected | self.CS.elected_pending)

    class Action(object):
        "one action"
        
        def __init__(self, E, action, msg):
            "create an action"
            self.E = E
            self.action = action
            self.msg = msg
            self.round = E.round
            CS = self.CS = E.CS.copy()
            self.votes = sum([CS.vote(c) for c in (CS.elected | CS.hopeful | CS.elected_pending)], E.V0)
            self.quota = E.quota
            self.surplus = E.V(E.surplus)
            if E.rule.method() == 'meek':
                self.residual = E.residual
            elif E.rule.method() == 'wigm':
                #
                #  this is expensive in a big election, so we've done a little optimization
                #
                self.nt_votes = sum((b.vote for b in E.ballots if b.exhausted), E.V0)
                self.h_votes = sum((c.vote for c in CS.hopeful), E.V0)
                self.e_votes = sum((c.vote for c in CS.elected), E.V0)
                self.d_votes = sum((c.vote for c in CS.elected_pending if c not in CS.elected), E.V0)
                total = self.e_votes + self.d_votes + self.h_votes + self.nt_votes
                #  wigm residual is votes lost due to rounding
                self.residual = E.V(E.nBallots) - total
            elif E.rule.method() == 'qpq':
                self.votes = E.votes
                self.ta = E.ta
                self.tx = E.tx
                self.surplus = '-'
            
        def signature(self):
            "return an action signature"

            E = self.E
            V = E.V
            CS = self.CS
            candidates = E.eligible.byBallotOrder() # report in ballot order
            
            #  dump a line of data
            #
            if self.action not in ('elect', 'defeat', 'tie', 'final'):
                return ''
            tag = self.action[0]
            round = 'F' if self.action == 'final' else self.round
            r = [round, tag, V(self.quota)]
            if E.rule.method() == 'meek':
                r.extend([V(self.votes), V(self.surplus), V(self.residual)])
            elif E.rule.method() == 'wigm':
                votes = self.e_votes + self.d_votes + self.h_votes
                total = votes + self.nt_votes + self.residual
                r.extend([V(total), V(votes), V(self.nt_votes), V(self.residual)])
            elif E.rule.method() == 'qpq':
                pass

            for c in candidates:
                r.append(c.nick)
                r.append(CS.code(c))
                r.append(V(CS.vote(c)))
                if E.rule.method() == 'meek': r.append(V(CS.kf(c)))

            r = [str(item) for item in r]
            return ':'.join(r) + '\n'

        def report(self):
            "report an action"
            if self.action == 'log':
                return "\t%s\n" % self.msg
            if self.action == 'round':
                return "Round %d:\n" % self.round
            E = self.E
            V = E.V
            CS = self.CS
            s = 'Action: %s\n' % (self.msg)
            if self.action in ('elect', 'defeat', 'transfer'):
                for c in CS.elected:
                    s += '\tElected:  %s (%s)\n' % (c, CS.vote(c))
                for c in CS.elected_pending:
                    if c not in CS.elected:
                        s += '\tPending:  %s (%s)\n' % (c, CS.vote(c))
                for c in CS.hopeful:
                    s += '\tHopeful:  %s (%s)\n' % (c, CS.vote(c))
                for c in (c for c in CS.defeated if CS.vote(c) > E.V0):
                    s += '\tDefeated: %s (%s)\n' % (c, CS.vote(c))
                c0 = [c.name for c in CS.defeated if CS.vote(c) == E.V0]
                if c0:
                    s += '\tDefeated: %s (%s)\n' % (', '.join(c0), E.V0)
            if E.rule.method() == 'meek':
                s += '\tQuota: %s\n' % V(self.quota)
                s += '\tVotes: %s\n' % V(self.votes)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V((self.votes + self.residual))
                s += '\tSurplus: %s\n' % V(self.surplus)
            elif E.rule.method() == 'wigm':
                s += '\tElected votes: %s\n' % V(self.e_votes)
                if self.d_votes:
                    s += '\tElection-deferred votes: %s\n' % V(self.d_votes)
                s += '\tHopeful votes: %s\n' % V(self.h_votes)
                s += '\tNontransferable votes: %s\n' % V(self.nt_votes)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V(self.e_votes + self.d_votes + self.h_votes + self.nt_votes + self.residual)
                s += '\tSurplus: %s\n' % V(self.surplus)
            elif E.rule.method() == 'qpq':
                s += '\tCandidates elected by active ballots: %s\n' % self.ta
                s += '\tCandidates elected by inactive ballots: %s\n' % self.tx
            return s
            
        def dump(self, header=False):
            "dump an action"

            E = self.E
            V = E.V
            CS = self.CS
            s = ''
            candidates = E.eligible.byBallotOrder() # report in ballot order
            
            #  return a header line if requested
            #
            if header:
                if E.rule.method() == 'meek':
                    h = ['R', 'Quota', 'Votes', 'Surplus', 'Residual']
                elif E.rule.method() == 'wigm':
                    h = ['R', 'Quota', 'Total', 'Votes', 'Non-Transferable', 'Residual']
                elif E.rule.method() == 'qpq':
                    h = ['R', 'Quota']

                for c in candidates:
                    h += ['%s.name' % c.cid]
                    h += ['%s.state' % c.cid]
                    h += ['%s.vote' % c.cid]
                    if E.rule.method() == 'meek': h += ['%s.kf' % c.cid]
                h = [str(item) for item in h]
                s += '\t'.join(h) + '\n'
                return s
            
            #  dump a line of data
            #
            if self.action in ('round', 'log', 'iterate'):
                r = [self.round, self.msg]
            else:
                round = 'F' if self.action == 'final' else self.round
                if E.rule.method() == 'meek':
                    r = [round, V(self.quota), V(self.votes), V(self.surplus), V(self.residual)]
                elif E.rule.method() == 'wigm':
                    votes = self.e_votes + self.d_votes + self.h_votes
                    total = votes + self.nt_votes + self.residual
                    r = [round, V(self.quota), V(total), V(votes), V(self.nt_votes), V(self.residual)]
                elif E.rule.method() == 'qpq':
                    r = [round, V(self.quota)]

                for c in candidates:
                    r.append(c.name)
                    r.append(CS.code(c))
                    r.append(V(CS.vote(c)))
                    if E.rule.method() == 'meek': r.append(V(CS.kf(c)))

            r = [str(item) for item in r]
            s += '\t'.join(r) + '\n'
            return s

    class Ballot(object):
        "one ballot"
        
        __slots__ = ('E', 'multiplier', 'index', 'weight', 'residual', 'ranking')
        
        def __init__(self, E, multiplier=1, ranking=None):
            "create a ballot"
            self.E = E
            self.multiplier = E.V(multiplier)  # number of ballots like this
            self.index = 0                # current ranking
            self.weight = E.V1            # initial weight
            self.residual = E.V0          # untransferable weight
            self.ranking = ranking

        def transfer(self):
            "advance index to next candidate on this ballot; return True if exists"
            while self.index < len(self.ranking) and self.topCand not in self.E.CS.hopeful:
                self.index += 1
            return not self.exhausted

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
            return self.E.candidates[self.ranking[self.index]] if self.index < len(self.ranking) else None
        
        @property
        def vote(self):
            "return total vote of this ballot"
            if self.multiplier == self.E.V1:
                return self.weight  # faster
            return self.weight * self.multiplier
            

class Candidate(object):
    '''
    a candidate
    
    A Candidate object is immutable, and shared across Rounds.
    '''

    def __init__(self, E, cid, ballotOrder, tieOrder, cname, cnick=None):
        "new candidate"
        self.E = E
        self.cid = cid              # candidate id
        self.order = ballotOrder    # ballot order
        self.tieOrder = tieOrder    # tie-breaking order
        self.name = cname           # candidate name
        self.nick = str(cid) if cnick is None else str(cnick)

    #  get/set vote total of this candidate
    #  vote counts are held in CandidateState
    #
    def getvote(self):
       "get current vote for candidate"
       return self.E.CS._vote[self.cid]
    def setvote(self, newvote):
        "set vote for candidate"
        self.E.CS._vote[self.cid] = newvote
    vote = property(getvote, setvote)
    
    @property
    def surplus(self):
        "return candidate's current surplus vote"
        s = self.vote - self.E.quota
        return self.E.V0 if s < self.E.V0 else s
        
    #  get/set keep factor of this candidate
    #  keep factors are held in CandidateState
    #
    def getkf(self):
       "get current keep factor for candidate"
       if not self.E.CS._kf: return None
       return self.E.CS._kf[self.cid]
    def setkf(self, newkf):
        "set keep factor for candidate"
        self.E.CS._kf[self.cid] = newkf
    kf = property(getkf, setkf)
    quotient = property(getkf, setkf)   # overload kf with QPQ quotient

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

class CandidateSet(set):
    '''
    sets of candidates
    
    special methods are provided to keep the results from escaping the CandidateSet class
    '''
    def byVote(self, CS=None):
        "list of candidates sorted by vote, ascending"
        if CS is None:
            return sorted(self, key=lambda c: (c.vote, c.order))
        return sorted(self, key=lambda c: (CS.vote(c), c.order))

    def byBallotOrder(self):
        "list of candidates sorted by ballot order"
        return sorted(self, key=lambda c: c.order)

    def byTieOrder(self):
        "list of candidates sorted by tie-break order"
        return sorted(self, key=lambda c: c.tieOrder)

    def __or__(self, other):
        "union"
        return CandidateSet(set(self) | set(other))

    def __and__(self, other):
        "intersection"
        return CandidateSet(set(self) & set(other))

    def __sub__(self, other):
        "difference"
        return CandidateSet(set(self) - set(other))

    def __iter__(self):
        "iterate CandidateSet in ballot order"
        return iter(sorted(set(self), key=lambda c: c.order))

    def __str__(self):
        "return list of candidate names"
        return ','.join(str(c) for c in self)

class CandidateState(object):
    '''
    per-round candidate state
    
    vote: get candidate vote
    kf: get candidate keep factor
    hopeful: the set of hopeful candidates
    elected: the set of elected candidates
    defeated: the set of defeated candidates
    withdrawn: access to Election's list of withdrawn candidates
    elected_pending: a set of elected candidates pending transfer (WIGM, not Meek)
    defeated_pending: a set of defeated candidates pending transfer (WIGM, not Meek)
    '''

    def __init__(self, E):
        "create candidate-state object"
        
        self.E = E

        self._vote = dict()   # votes by candidate cid
        self._kf = dict()     # keep factor by candidate cid
        
        self.hopeful = CandidateSet()
        self.elected_pending = CandidateSet()
        self.elected = CandidateSet()
        self.defeated_pending = CandidateSet()
        self.defeated = CandidateSet()

    def code(self, c):
        "return a one-letter state code for a candidate"
        if c in self.withdrawn: return 'W'
        if c in self.hopeful: return 'H'
        if self.E.rule.method() == 'wigm' and c in self.elected_pending: return 'e'
        if c in self.elected: return 'E'
        if self.E.rule.method() == 'wigm' and c in self.defeated_pending: return 'd'
        if c in self.defeated: return 'D'
        return '?'  # pragma: no cover

    @property
    def withdrawn(self):
        "interface to E.withdrawn for consistency"
        return self.E.withdrawn

    @property
    def hopefulOrElected(self):
        "return combined list of hopeful and elected candidates"
        return self.hopeful | self.elected | self.elected_pending

    def vote(self, c):
        "return candidate vote total"
        return self._vote[c.cid]

    def kf(self, c):
        "return candidate keep factor"
        return self._kf[c.cid]

    def copy(self):
        "return a copy of ourself"
        CS = CandidateState(self.E)
        
        CS._vote = self._vote.copy()
        CS._kf = self._kf.copy()
        
        CS.hopeful = CandidateSet(self.hopeful)
        CS.elected = CandidateSet(self.elected)
        CS.defeated = CandidateSet(self.defeated)
        CS.elected_pending = CandidateSet(self.elected_pending)
        CS.defeated_pending = CandidateSet(self.defeated_pending)
        return CS

    #  add a candidate to the election
    #
    def addCandidate(self, c, isWithdrawn=False):
        "add a candidate"
        if isWithdrawn:
            self.E.withdrawn.add(c)
            self.E.log("Add withdrawn: %s" % c.name)
        else:
            self.E.eligible.add(c)
            self.hopeful.add(c)
            self.E.log("Add eligible: %s" % c.name)

    def elect(self, cand, msg='Elect', defer=False):
        "elect a candidate"
        cand = CandidateSet([cand] if isinstance(cand, Candidate) else cand)
        for c in cand:
            self.hopeful.discard(c)
            if not defer:
                self.elected.add(c)
            if self.E.rule.method() == 'wigm':
                self.elected_pending.add(c)
        if not defer:
            self.E.logAction('elect', "%s: %s" % (msg, cand))

    def unelect(self, c):
        "unelect a candidate (qpq restart)"
        self.hopeful.add(c)
        self.elected.remove(c)
        self.elected_pending.discard(c)

    def defeat(self, cand, msg='Defeat'):
        "defeat a candidate"
        cand = CandidateSet([cand] if isinstance(cand, Candidate) else cand)
        for c in cand:
            self.hopeful.remove(c)
            self.defeated.add(c)
            if self.E.rule.method() == 'wigm':
                self.defeated_pending.add(c)
        self.E.logAction('defeat', "%s: %s" % (msg, cand))
