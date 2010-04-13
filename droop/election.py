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

import sys
import values
import droop
from droop.common import ElectionError

class Election(object):
    '''
    container for an election
    '''
    
    def __init__(self, rule, electionProfile, options=dict()):
        "create an election from the incoming election profile"

        self.rule = rule # a class
        options = self.rule.options(options)     # allow rule to process options
        self.V = values.ArithmeticClass(options) # then set arithmetic
        self.V0 = self.V(0)  # constant zero for efficiency
        self.V1 = self.V(1)  # constant one for efficiency
        self.electionProfile = electionProfile

        self.rounds = [self.Round(self)]
        self.R0 = self.R = self.rounds[0]
        
        self.eligible = list()
        self.withdrawn = list()
        self.candidates = dict()
        
        self.elected = None  # for communicating results
        
        #  create candidate objects for candidates in election profile
        #
        for cid in sorted(electionProfile.eligible | electionProfile.withdrawn):
            c = Candidate(self, cid, electionProfile.candidateOrder(cid), electionProfile.candidateName(cid))
            if c.cid in self.candidates.keys():
                raise ElectionError('duplicate candidate id: %s (%s)' % (c.cid, c.name))
            self.candidates[cid] = c
            c.vote = self.V0
            #
            #  and add the candidate to round 0
            #
            self.R0.CS.addCandidate(c, isWithdrawn=cid in electionProfile.withdrawn)
        
        #  update tiebreaking order if one was specified via profile =tie option
        #
        if electionProfile.tieOrder:
            for c in self.candidates.values():
                c.tieOrder = electionProfile.tieOrder[c.cid]

        #  create a ballot object (ranking candidate IDs) from the profile rankings of candidate IDs
        #  only eligible (not withdrawn) will be added
        #
        self.ballots = list()
        for bl in electionProfile.ballotLines:
            self.ballots.append(self.Ballot(self, bl.multiplier, bl.ranking))

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
        
    def count(self):
        "count the election"
        self.rule.count(self)
        self.R.rollup(self.rule.method())             # roll up last round
        self.elected = self.rounds[-1].CS.elected   # collect set of elected candidates
        
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
        reportMeek = self.rule.method() == 'meek'
        s = "\nElection: %s\n\n" % self.title
        s += "\tDroop package: %s v%s\n" % (droop.common.droopName, droop.common.droopVersion)
        s += "\tRule: %s\n" % self.rule.info()
        s += "\tArithmetic: %s\n" % self.V.info
        s += "\tSeats: %d\n" % self.nSeats
        s += "\tBallots: %d\n" % self.nBallots
        s += "\tQuota: %s\n" % self.V(self.R0.quota)
        if reportMeek:
            s += "\tOmega: %s\n" % self.rule._omega
        if self.electionProfile.source:
            s += "Source: %s\n" % self.electionProfile.source
        if self.electionProfile.comment:
            s += "{%s}\n" % self.electionProfile.comment
        s += '\n'
        if intr:
            s += "\t** Count terminated prematurely by user interrupt **\n\n"
            self.R.log('** count interrupted; this round is incomplete **')
        s += self.V.report()
        for round in self.rounds:
            s += "Round %d:\n" % round.n
            s += round.report(reportMeek)
        return s

    def dump(self):
        "dump election by round"
        reportMeek = self.rule.method() == 'meek'
        s = ''
        for round in self.rounds:
            s += round.dump(reportMeek)
        return s

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - self.R.CS.nElected

    def transferSurplus(self, c):
        "WIGM: transfer surplus for elected candidate"
        vote = c.vote
        surplus = vote - self.R.quota
        for b in (b for b in self.ballots if b.topCand == c):
            b.weight = (b.weight * surplus) / vote

    def countTopVotes(self):
        "count first-place votes"
        if self.rule.method() == 'meek':
            for b in (b for b in self.ballots if b.topCand):
                b.topCand.vote += self.V(b.multiplier)
        else:
            for b in (b for b in self.ballots if not b.exhausted):
                b.topCand.vote = b.topCand.vote + b.vote

    def transferBallots(self, kt):
        "perform a Meek/Warren transfer of votes on all ballots"
        V0 = self.V0
        candidate = self.candidate
        self.R.residual = V0
        for b in self.ballots:
            b.weight = self.V1
            b.residual = self.V(b.multiplier)
            for c in (candidate(cid) for cid in b.ranking):
                if c.kf:
                    keep, b.weight = kt(c.kf, b.weight)
                    c.vote += keep * b.multiplier      # b.multiplier is an int
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
    
        def transfer(self, c, val, msg='Transfer'):
            "transfer ballots with candidate c at top"
            self.log("%s: %s (%s)" % (msg, c.name, self.E.V(val)))
            cid = c.cid
            ballots = self.E.ballots
            for b in (b for b in ballots if b.topCid == cid):
                b.transfer(self.CS.hopeful)
            if c in self.CS.pending:
                self.CS.pending.remove(c)

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

        def report(self, reportMeek):
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
            s += '\tHopeful: %s\n' % (" ".join([c.name for c in CS.sortByOrder(CS.hopeful)]) or 'None')
            s += '\tElected: %s\n' % (" ".join([c.name for c in CS.sortByOrder(CS.elected)]) or 'None')
            s += '\tDefeated: %s\n' % (" ".join([c.name for c in CS.sortByOrder(CS.defeated)]) or 'None')
            if reportMeek:
                s += '\tQuota: %s\n' % V(self.quota)
                s += '\tVotes: %s\n' % V(self.votes)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V((self.votes + self.residual))
                s += '\tSurplus: %s\n' % V(self.surplus)
            else: # wigm
                s += '\tElected votes (not pending) %s\n' % V(self.evotes)
                s += '\tTop-rank votes (elected): %s\n' % V(self.pvotes)
                s += '\tTop-rank votes (hopeful): %s\n' % V(self.hvotes)
                s += '\tNontransferable votes: %s\n' % V(self.nontransferable)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V(self.evotes + self.pvotes + self.hvotes + self.nontransferable + self.residual)
                s += '\tSurplus: %s\n' % V(self.surplus)
            E.R = saveR
            return s
            
        def dump(self, reportMeek):
            "dump a round"

            E = self.E
            V = E.V
            CS = self.CS
            saveR, E.R = E.R, self # provide reporting context
            s = ''
            
            candidates = CS.sortByOrder(E.eligible) # report in ballot order

            #  if round 0, include a header line
            #
            if self.n == 0:
                h = ['R', 'Quota', 'Votes', 'Surplus']
                if reportMeek: h += ['Residual']
                for c in candidates:
                    cid = c.cid
                    h += ['%s.name' % cid]
                    h += ['%s.state' % cid]
                    h += ['%s.vote' % cid]
                    if reportMeek: h += ['%s.kf' % cid]
                h = [str(item) for item in h]
                s += '\t'.join(h) + '\n'
            
            #  dump a line of data
            #
            r = [self.n, V(self.quota), V(self.votes), V(self.surplus)]
            if reportMeek: r.append(V(self.residual))
            for c in candidates:
                cid = c.cid
                r.append(c.name)
                if self.n:
                    r.append('W' if c in CS.withdrawn else 'H' if c in CS.hopeful else 'P' if not reportMeek and c in CS.pending else 'E' if c in CS.elected else 'D' if c in CS.defeated else '?') # state
                    r.append(V(c.vote))
                    if reportMeek: r.append(V(c.kf))
                else:
                    r.append('W' if c in CS.withdrawn else 'H') # state
                    r.append(V(c.vote)) # vote
                    if reportMeek: r.append('-') # kf
                
            r = [str(item) for item in r]
            s += '\t'.join(r) + '\n'
            E.R = saveR
            return s

    class Ballot(object):
        "one ballot"
        
        __slots__ = ('E', 'multiplier', 'index', 'weight', 'residual', 'ranking')
        
        def __init__(self, E, multiplier=1, ranking=None):
            "create a ballot"
            if E is not None:  # E=None signals a copy operation
                self.E = E
                self.multiplier = multiplier  # number of ballots like this
                self.index = 0                # current ranking
                self.weight = E.V1            # initial weight
                self.residual = E.V0          # untransferable weight
                self.ranking = ranking

        def copy(self):
            "return a copy of this ballot"
            b = Election.Ballot(None)
            b.E = self.E
            b.multiplier = self.multiplier
            b.index = self.index
            b.weight = self.weight
            b.residual = self.residual
            b.ranking = self.ranking    # share the immutable tuple of ranking
            return b
    
        def transfer(self, hopeful, msg='Transfer'):
            "advance index to next candidate on this ballot; return True if exists"
            while self.index < len(self.ranking) and self.topCand not in hopeful:
                self.index += 1
            return not self.exhausted
    
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
            if self.multiplier == 1:
                return self.weight  # faster
            return self.weight * self.multiplier
            
'''
Candidate and CandidateState classes

Candidate holds a candidate ID and uses it to manage state in CandidateState.
CandidateState contains the per-round candidate state.

copyright 2010 by Jonathan Lundell
'''

class Candidate(object):
    '''
    a candidate
    
    A Candidate object is immutable, and shared across Rounds.
    '''

    def __init__(self, E, cid, order, cname):
        "new candidate"
        self.E = E
        self.cid = cid        # candidate id
        self.order = order    # ballot order
        self.name = cname     # candidate name
        self.tieOrder = order # default tiebreaking order

    #  get/set vote total of this candidate
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
    #
    def getkf(self):
       "get current keep factor for candidate"
       if not self.E.R.CS._kf: return None
       return self.E.R.CS._kf[self.cid]
    def setkf(self, newkf):
        "set keep factor for candidate"
        self.E.R.CS._kf[self.cid] = newkf
    kf = property(getkf, setkf)

    def __str__(self):
        "stringify"
        return self.name

    def __eq__(self, other):
        "test for equality of cid"
        if isinstance(other, str):
            return self.cid == other
        if other is None:
            return False
        return self.cid == other.cid

class CandidateState(object):
    '''
    per-round candidate state
    
    vote: get candidate vote
    kf: get candidate keep factor
    hopeful: the list of hopeful candidates
    elected: the list of elected candidates
    defeated: the list of defeated candidates
    withdrawn: access to Election's list of withdrawn candidates
    pending: a list of elected candidates pending transfer (WIGM, not Meek)
    isHopeful, etc: boolean test of a single candidate
    nHopeful, etc: number of candidates in set (properties)
    '''

    def __init__(self, E):
        "create candidate-state object"
        
        self.E = E

        self._vote = dict()   # votes by candidate cid
        self._kf = dict()     # keep factor by candidate cid
        
        self.hopeful = list()
        self.pending = list()
        self.elected = list()
        self.defeated = list()

    @property
    def withdrawn(self):
        "interface to E.withdrawn for consistency"
        return self.E.withdrawn

    @property
    def hopefulOrElected(self):
        "return combined list of hopeful and elected candidates"
        return self.hopeful + self.elected

    @property
    def hopefulOrPending(self):
        "return combined list of hopeful and transfer-pending candidates"
        return self.hopeful + self.pending

    def copy(self):
        "return a copy of ourself"
        CS = CandidateState(self.E)
        
        CS._vote = self._vote.copy()
        CS._kf = self._kf.copy()
        
        CS.hopeful = list(self.hopeful)
        CS.elected = list(self.elected)
        CS.defeated = list(self.defeated)
        CS.pending = list(self.pending)
        return CS

    #  add a candidate to the election
    #
    def addCandidate(self, c, isWithdrawn=False):
        "add a candidate"
        if isWithdrawn:
            self.E.withdrawn.append(c)
            self.E.R.log("Add withdrawn: %s" % c.name)
        else:
            self.E.eligible.append(c)
            self.hopeful.append(c)
            self.E.R.log("Add eligible: %s" % c.name)

    def elect(self, c, msg='Elect'):
        "elect a candidate"
        self.hopeful.remove(c)
        self.elected.append(c)
        self.pending.append(c)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, self.E.V(c.vote)))
    def defeat(self, c, msg='Defeat'):
        "defeat a candidate"
        self.hopeful.remove(c)
        self.defeated.append(c)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, self.E.V(c.vote)))

    def vote(self, c, r=None):
        "return vote for candidate in round r (default=current)"
        if r is None: return self._vote[c.cid]
        return self.E.rounds[r].CS._vote[c.cid]

    #  return count of candidates in requested state
    #
    @property
    def nHopeful(self):
        "return count of hopeful candidates"
        return len(self.hopeful)
    @property
    def nPending(self):
        "return count of transfer-pending candidates"
        return len(self.pending)
    @property
    def nElected(self):
        "return count of elected candidates"
        return len(self.elected)
    @property
    def nHopefulOrElected(self):
        "return count of hopeful+elected candidates"
        return self.nHopeful + self.nElected
    @property
    def nDefeated(self):
        "return count of defeated candidates"
        return len(self.defeated)
    @property
    def nWithdrawn(self):
        "return count of withdrawn candidates"
        return len(self.E.withdrawn)
        
    def sortByVote(self, collection):
        "sort a collection of candidates by vote"
        # keep the result stable by ballot order
        return sorted(collection, key=lambda c: (c.vote, c.order))

    def sortByOrder(self, collection):
        "sort a collection of candidates by ballot order"
        return sorted(collection, key=lambda c: c.order)

    def sortByTieOrder(self, collection):
        "sort a collection of candidates by tieOrder"
        return sorted(collection, key=lambda c: c.tieOrder)
