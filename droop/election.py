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

        self.rounds = [self.Round(self)]
        self.R0 = self.R = self.rounds[0]
        
        self.eligible = CandidateSet()
        self.withdrawn = CandidateSet()
        self.candidates = dict()  # cid: Candidate
        
        self.elected = None  # for communicating results
        
        #  create candidate objects for candidates in election profile
        #
        for cid in sorted(electionProfile.eligible | electionProfile.withdrawn):
            c = Candidate(self, cid, electionProfile.candidateOrder(cid), 
                electionProfile.tieOrder[cid],
                electionProfile.candidateName(cid),
                electionProfile.nickName[cid])
            self.candidates[cid] = c
            c.vote = self.V0
            #
            #  and add the candidate to round 0
            #
            self.R0.CS.addCandidate(c, isWithdrawn=cid in electionProfile.withdrawn)

        #  create a ballot object (ranking candidate IDs) from the profile rankings of candidate IDs
        #  withdrawn candidates have been removed alreay
        #
        self.ballots = list()
        for bl in electionProfile.ballotLines:
            if bl.ranking:  # if only withdrawn candidates
                self.ballots.append(self.Ballot(self, bl.multiplier, bl.ranking))

    def count(self):
        "count the election"
        self.rule.count(self)
        self.R.rollup(self.rule.method())           # roll up last round
        self.elected = self.rounds[-1].CS.elected.byBallotOrder()
        
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
        
    def newRound(self):
       "add a round"
       self.R.rollup(self.rule.method())      # capture summaries of ballots
       self.rounds.append(self.Round(self, copy=True))
       self.R = self.rounds[-1]
       return self.R

    def log(self, msg):
        "log a message to the current round"
        self.R.log(msg)

    def prog(self, msg):
        "log to the console (immediate output)"
        sys.stdout.write(msg)
        sys.stdout.flush()

    def report(self, intr=False):
        "report election by round"
        s = "\nElection: %s\n\n" % self.title
        s += "\tDroop package: %s v%s\n" % (droop.common.droopName, droop.common.droopVersion)
        s += "\tRule: %s\n" % self.rule.info()
        s += "\tArithmetic: %s\n" % self.V.info
        s += "\tSeats: %d\n" % self.nSeats
        s += "\tBallots: %d\n" % self.nBallots
        s += "\tQuota: %s\n" % self.V(self.R0.quota)
        if self.rule.method() == 'meek':
            s += "\tOmega: %s\n" % self.rule._omega
        if self.electionProfile.source:
            s += "Source: %s\n" % self.electionProfile.source
        if self.electionProfile.comment:
            s += "{%s}\n" % self.electionProfile.comment
        s += '\n'
        if intr:    # pragma: no cover
            s += "\t** Count terminated prematurely by user interrupt **\n\n"
            self.R.log('** count interrupted; this round is incomplete **')
        s += self.V.report()
        for round in self.rounds:
            s += "Round %d:\n" % round.n
            s += round.report()
        return s

    def dump(self):
        "dump election by round"
        s = ''
        for round in self.rounds:
            s += round.dump()
        return s

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - len(self.R.CS.elected)

    def transferBallots(self, c, msg='Transfer', tf=None):
        "WIGM: transfer ballots for elected or defeated candidate"
        vote = c.vote
        cid = c.cid
        ballots = self.ballots
        
        if c in self.R.CS.elected:
            self.R.CS.pending.remove(c)
            surplus = vote - self.R.quota
            for b in (b for b in ballots if b.topCid == cid):
                b.weight = tf(self.V, b.weight, surplus, vote)
                if b.transfer():
                    b.topCand.vote += b.vote
            val = surplus
            c.vote = self.R.quota
        else:
            for b in (b for b in ballots if b.topCid == cid):
                if b.transfer():
                    b.topCand.vote += b.vote
            val = vote
            c.vote = self.V0
        self.log("%s: %s (%s)" % (msg, c.name, self.V(val)))

    def distributeVotes(self, kt):
        "perform a Meek/Warren distribution of votes on all ballots"
        V0 = self.V0
        candidate = self.candidate
        self.R.residual = V0
        for b in self.ballots:
            b.weight = self.V1
            b.residual = b.multiplier
            for c in (candidate(cid) for cid in b.ranking):
                if c.kf:
                    keep, b.weight = kt(c.kf, b.weight)
                    c.vote += keep * b.multiplier
                    b.residual -= keep * b.multiplier  # residual value of ballot
                    if b.weight <= V0:
                        break
            self.R.residual += b.residual  # residual for round

    class Round(object):
        "one election round"
        
        def __init__(self, E, copy=False):
            "create a round"
            self.E = E
            if not copy:
                #
                #  create round 0: the initial state
                #  quota & ballots are filled in later
                #
                self.n = 0
                self.CS = CandidateState(E)
                self.quota = None
            else:
                #
                #  subsequent rounds are copies,
                #  so we can look back at previous rounds
                #
                #  E.R and E.CS are the current round and candidate states
                #
                previous = E.R
                self.n = previous.n + 1
                self.CS = previous.CS.copy()
                self.quota = previous.quota
            self.residual = E.V0
            self.votes = E.V0
            self.surplus = E.V0
            self.pvotes = E.V0
            self.hvotes = E.V0
            self.nontransferable = E.V0
            self.evotes = E.V0
            self._log = [] # list of log messages
    
        def rollup(self, method):
            "roll up stats from ballots"
            E = self.E
            CS = self.CS
            if method == 'wigm':
                #
                #  this is expensive in a big election, so we've done a little optimization
                #
                pvotes = E.V0  # elected pending transfer
                hvotes = E.V0  # top-ranked hopeful
                nontransferable = E.V0
                elected = [c.cid for c in CS.elected]
                hopeful = [c.cid for c in CS.hopeful]
                for b in E.ballots:
                    if b.exhausted:
                        nontransferable += b.vote
                    else:
                        topCid = b.topCid
                        if topCid in elected:
                            pvotes += b.vote
                        elif topCid in hopeful:
                            hvotes += b.vote
                self.pvotes = pvotes
                self.hvotes = hvotes
                self.nontransferable = nontransferable
                self.evotes = E.V0
                for c in CS.elected:
                    if not c in CS.pending:
                        self.evotes += E.R.quota
                total = self.evotes + self.pvotes + self.hvotes + self.nontransferable
                #  wigm residual is votes lost due to rounding
                self.residual = E.V(E.nBallots) - total
            
        def log(self, msg):
            "log a message"
            self._log.append(msg)

        def report(self):
            "report a round"
            E = self.E
            V = E.V
            CS = self.CS
            saveR, E.R = E.R, self # provide reporting context
            s = ''
            for line in self._log:
                s += '\t%s\n' % line
            if self._log:
                s += '\t...\n'
            s += '\tHopeful: %s\n' % (", ".join([c.name for c in CS.hopeful.byBallotOrder()]) or 'None')
            s += '\tElected: %s\n' % (", ".join([c.name for c in CS.elected.byBallotOrder()]) or 'None')
            s += '\tDefeated: %s\n' % (", ".join([c.name for c in CS.defeated.byBallotOrder()]) or 'None')
            if E.rule.method() == 'meek':
                s += '\tQuota: %s\n' % V(self.quota)
                s += '\tVotes: %s\n' % V(self.votes)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V((self.votes + self.residual))
                s += '\tSurplus: %s\n' % V(self.surplus)
            elif E.rule.method() == 'wigm':
                s += '\tElected votes (not pending) %s\n' % V(self.evotes)
                s += '\tTop-rank votes (elected): %s\n' % V(self.pvotes)
                s += '\tTop-rank votes (hopeful): %s\n' % V(self.hvotes)
                s += '\tNontransferable votes: %s\n' % V(self.nontransferable)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V(self.evotes + self.pvotes + self.hvotes + self.nontransferable + self.residual)
                s += '\tSurplus: %s\n' % V(self.surplus)
            elif E.rule.method() == 'qpq':
                s += '\tCandidates elected by active ballots: %s\n' % self.ta
                s += '\tCandidates elected by inactive ballots: %s\n' % self.tx
            E.R = saveR
            return s
            
        def dump(self):
            "dump a round"

            E = self.E
            V = E.V
            CS = self.CS
            saveR, E.R = E.R, self # provide reporting context
            s = ''
            
            candidates = E.eligible.byBallotOrder() # report in ballot order

            #  if round 0, include a header line
            #
            if self.n == 0:
                h = ['R', 'Quota', 'Votes', 'Surplus']
                if E.rule.method() == 'meek': h += ['Residual']
                for c in candidates:
                    cid = c.cid
                    h += ['%s.name' % cid]
                    h += ['%s.state' % cid]
                    h += ['%s.vote' % cid]
                    if E.rule.method() == 'meek': h += ['%s.kf' % cid]
                h = [str(item) for item in h]
                s += '\t'.join(h) + '\n'
            
            #  dump a line of data
            #
            r = [self.n, V(self.quota), V(self.votes), V(self.surplus)]
            if E.rule.method() == 'meek': r.append(V(self.residual))
            for c in candidates:
                cid = c.cid
                r.append(c.name)
                if self.n:
                    r.append('W' if c in CS.withdrawn else 'H' if c in CS.hopeful else 'P' if E.rule.method() == 'wigm' and c in CS.pending else 'E' if c in CS.elected else 'D' if c in CS.defeated else '?') # state
                    r.append(V(c.vote))
                    if E.rule.method() == 'meek': r.append(V(c.kf))
                else:
                    r.append('W' if c in CS.withdrawn else 'H') # state
                    r.append(V(c.vote)) # vote
                    if E.rule.method() == 'meek': r.append('-') # kf
                
            r = [str(item) for item in r]
            s += '\t'.join(r) + '\n'
            E.R = saveR
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
            while self.index < len(self.ranking) and self.topCand not in self.E.R.CS.hopeful:
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
        def topCid(self):
            "return top candidate ID, or None if exhausted"
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
       return self.E.R.CS._vote[self.cid]
    def setvote(self, newvote):
        "set vote for candidate"
        self.E.R.CS._vote[self.cid] = newvote
    vote = property(getvote, setvote)
    
    @property
    def surplus(self):
        "return candidate's current surplus vote"
        s = self.vote - self.E.R.quota
        return self.E.V0 if s < self.E.V0 else s
        
    #  get/set keep factor of this candidate
    #  keep factors are held in CandidateState
    #
    def getkf(self):
       "get current keep factor for candidate"
       if not self.E.R.CS._kf: return None
       return self.E.R.CS._kf[self.cid]
    def setkf(self, newkf):
        "set keep factor for candidate"
        self.E.R.CS._kf[self.cid] = newkf
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
    def byVote(self):
        "list of candidates sorted by vote, ascending"
        return sorted(self, key=lambda c: (c.vote, c.order))

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

class CandidateState(object):
    '''
    per-round candidate state
    
    vote: get candidate vote
    kf: get candidate keep factor
    hopeful: the set of hopeful candidates
    elected: the set of elected candidates
    defeated: the set of defeated candidates
    withdrawn: access to Election's list of withdrawn candidates
    pending: a set of elected candidates pending transfer (WIGM, not Meek)
    '''

    def __init__(self, E):
        "create candidate-state object"
        
        self.E = E

        self._vote = dict()   # votes by candidate cid
        self._kf = dict()     # keep factor by candidate cid
        
        self.hopeful = CandidateSet()
        self.pending = CandidateSet()
        self.elected = CandidateSet()
        self.defeated = CandidateSet()

    @property
    def withdrawn(self):
        "interface to E.withdrawn for consistency"
        return self.E.withdrawn

    @property
    def hopefulOrElected(self):
        "return combined list of hopeful and elected candidates"
        return self.hopeful | self.elected

    def copy(self):
        "return a copy of ourself"
        CS = CandidateState(self.E)
        
        CS._vote = self._vote.copy()
        CS._kf = self._kf.copy()
        
        CS.hopeful = CandidateSet(self.hopeful)
        CS.elected = CandidateSet(self.elected)
        CS.defeated = CandidateSet(self.defeated)
        CS.pending = CandidateSet(self.pending)
        return CS

    #  add a candidate to the election
    #
    def addCandidate(self, c, isWithdrawn=False):
        "add a candidate"
        if isWithdrawn:
            self.E.withdrawn.add(c)
            self.E.R.log("Add withdrawn: %s" % c.name)
        else:
            self.E.eligible.add(c)
            self.hopeful.add(c)
            self.E.R.log("Add eligible: %s" % c.name)

    def elect(self, c, msg='Elect', val=None):
        "elect a candidate"
        self.hopeful.remove(c)
        self.elected.add(c)
        self.pending.add(c)
        if val is None: val = self.E.V(c.vote)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, val))

    def unelect(self, c):
        "unelect a candidate (qpq restart)"
        self.hopeful.add(c)
        self.elected.remove(c)
        self.pending.remove(c)

    def defeat(self, c, msg='Defeat', val=None):
        "defeat a candidate"
        self.hopeful.remove(c)
        self.defeated.add(c)
        if val is None: val = self.E.V(c.vote)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, val))
