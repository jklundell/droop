'''
Generic Election Support

copyright 2010 by Jonathan Lundell

Top-level structure:

  A driver program (for example droop, the CLI) 
    1. creates an ElectionProfile from a ballot file,
    2. imports a Rule, 
    3. creates an Election(Rule, ElectionProfile, options),
    4. counts the election with Election.count(), and
    5. generates a report with Election.report().
  
  The options are used to override default Rule parameters, such as arithmetic.
'''

import sys
import values
import packages

class Election(object):
    '''
    container for an election
    '''
    rule = None      # election rule class
    V = None         # arithmetic method
    V0 = None        # constant zero
    V1 = None        # constant one
    rounds = None    # election rounds
    R0 = None        # round 0 (initial state)
    R = None         # current round
    eligible = None    # all the non-withdrawn candidates
    withdrawn = None   # all the withdrawn candidates
    _candidates = None # candidates by candidate ID
    
    class ElectionError(Exception):
        "error counting election"

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
        
        self.eligible = set()
        self.withdrawn = set()
        self._candidates = dict()
        #
        #  create candidate objects for candidates in election profile
        #
        for cid in electionProfile.eligible | electionProfile.withdrawn:
            c = Candidate(self, cid, electionProfile.candidateOrder(cid), electionProfile.candidateName(cid))
            if c.cid in self._candidates.keys():
                raise self.ElectionError('duplicate candidate id: %s (%s)' % (c.cid, c.name))
            self._candidates[cid] = c
            #
            #  add each candidate to either the eligible or withdrawn set
            #
            if cid in electionProfile.eligible:
                self.eligible.add(c)
            else:
                self.withdrawn.add(c)
            #
            #  and add the candidate to round 0
            #
            self.R0.C.addCandidate(c, isWithdrawn=cid in electionProfile.withdrawn)
        #
        #  create a ballot object (ranking candidate objects) from the profile rankings of candidate IDs
        #  only eligible (not withdrawn) will be added
        #
        for bl in electionProfile.ballotLines:
            self.R0.ballots.append(self.Ballot(self, bl.multiplier, bl.ranking))

    @classmethod
    def makehelp(cls):
        "build a dictionary of help strings on various subjects"
        helps = dict()
        helps['rule'] =  'available rules: %s' % ','.join(packages.electionRuleNames())
        for name in packages.electionRuleNames():
            packages.ruleByName[name].helps(helps, name)
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
        return self._candidates[cid]
        
    def count(self):
        "count the election"
        self.rule.count(self)
        
    def newRound(self):
       "add a round"
       self.rounds.append(self.Round(self))
       self.R = self.rounds[-1]
       self.R.prior = self.rounds[-2]
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
        reportMeek = self.rule.reportMode() == 'meek'
        s = "\nElection: %s\n\n" % self.title
        s += "\tRule: %s\n" % self.rule.info()
        s += "\tArithmetic: %s\n" % self.V.info
        s += "\tSeats: %d\n" % self.nSeats
        s += "\tBallots: %d\n" % self.nBallots
        s += "\tQuota: %s\n" % self.V(self.R0.quota)
        if reportMeek:
            s += "\tOmega: %s\n" % self.rule.omega
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
        reportMeek = self.rule.reportMode() == 'meek'
        s = ''
        for round in self.rounds:
            s += round.dump(reportMeek)
        return s

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - self.R.C.nElected

    class Round(object):
        "one election round"
        
        def __init__(self, E):
            "create a round"
            self.E = E
            if not E.R0:
                #
                #  create round 0: the initial state
                #  quota & ballots are filled in later
                #
                self.n = 0
                self.C = CandidateState(E)
                self.quota = None
                self.ballots = list()
            else:
                #
                #  subsequent rounds are copies,
                #  so we can look back at previous rounds
                #
                #  E.R and E.C are the current round and candidate states
                #
                previous = E.R
                self.n = previous.n + 1
                self.C = previous.C.copy()
                self.quota = previous.quota
                self.ballots = [b.copy() for b in previous.ballots]
            self.residual = E.V0
            self.votes = E.V0
            self.surplus = E.V0
            self._log = [] # list of log messages
    
        def transfer(self, c, val, msg='Transfer'):
            "transfer ballots with candidate c at top"
            self.log("%s: %s (%s)" % (msg, c.name, self.E.V(val)))
            for b in [b for b in self.ballots if b.topCand == c]:
                b.transfer(self.C.hopeful)
    
        def log(self, msg):
            "log a message"
            self._log.append(msg)
            
        def report(self, reportMeek):
            "report a round"
            E = self.E
            V = E.V
            C = self.C
            saveR, E.R = E.R, self # provide reporting context
            s = ''
            for line in self._log:
                s += '\t%s\n' % line
            if self._log:
                s += '\t...\n'
            s += '\tHopeful: %s\n' % (" ".join([c.name for c in C.sortByOrder(C.hopeful)]) or 'None')
            s += '\tElected: %s\n' % (" ".join([c.name for c in C.sortByOrder(C.elected)]) or 'None')
            s += '\tDefeated: %s\n' % (" ".join([c.name for c in C.sortByOrder(C.defeated)]) or 'None')
            if reportMeek:
                s += '\tQuota: %s\n' % V(E.R.quota)
                s += '\tVotes: %s\n' % V(E.R.votes)
                s += '\tResidual: %s\n' % V(E.R.residual)
                s += '\tTotal: %s\n' % V((E.R.votes + E.R.residual))
                s += '\tSurplus: %s\n' % V(E.R.surplus)
            else: # wigm
                pvotes = E.V0  # elected pending transfer
                hvotes = E.V0  # top-ranked hopeful
                nontransferable = E.V0
                for b in self.ballots:
                    if b.exhausted:
                        nontransferable += b.vote
                    else:
                        if b.topCand in C.elected:
                            pvotes += b.vote
                        elif b.topCand in C.hopeful:
                            hvotes += b.vote
                evotes = E.V0
                for c in C.elected:
                    if not c in C.pending:
                        evotes += E.R.quota
                total = evotes + pvotes + hvotes + nontransferable
                #  residual here (wigm) is votes lost due to rounding
                residual = E.V(E.nBallots) - total
                s += '\tElected votes (not pending) %s\n' % V(evotes)
                s += '\tTop-rank votes (elected): %s\n' % V(pvotes)
                s += '\tTop-rank votes (hopeful): %s\n' % V(hvotes)
                s += '\tNontransferable votes: %s\n' % V(nontransferable)
                s += '\tResidual: %s\n' % V(residual)
                s += '\tTotal: %s\n' % V(evotes + pvotes + hvotes + nontransferable + residual)

            E.R = saveR
            return s
            
        def dump(self, reportMeek):
            "dump a round"

            E = self.E
            saveR, E.R = E.R, self # provide reporting context
            V = E.V
            C = E.R.C
            s = ''
            
            candidates = C.sortByOrder(E.eligible) # report in ballot order
            #  if round 0, include a header line
            if self.n == 0:
                h = ['R', 'Q']
                if reportMeek: h += ['residual']
                for c in candidates:
                    cid = c.cid
                    h += ["'%s.name'" % cid]
                    h += ["'%s.state'" % cid]
                    h += ["'%s.vote'" % cid]
                    if reportMeek: h += ["'%s.kf'" % cid]
                h = [str(item) for item in h]
                s += ','.join(h) + '\n'
                
            r = [self.n, V(self.quota)]
            if reportMeek: r.append(V(self.residual))
            for c in candidates:
                cid = c.cid
                r.append(c.name)
                if self.n:
                    r.append('W' if c in C.withdrawn else 'H' if c in C.hopeful else 'P' if c in C.pending else 'E' if c in C.elected else 'D' if c in C.defeated else '?') # state
                    r.append(V(c.vote))
                    if reportMeek: r.append(V(c.kf))
                else:
                    r.append('W' if c in C.withdrawn else 'H') # state
                    r.append(V(c.vote)) # vote
                    if reportMeek: r.append("'-'") # kf
                
            r = [str(item) for item in r]
            s += ','.join(r) + '\n'
            E.R = saveR
            return s

    class Ballot(object):
        "one ballot"
        
        def __init__(self, E, multiplier=1, ranking=None):
            "create a ballot"
            if E is not None:  # E=None signals a copy operation
                self.multiplier = multiplier  # number of ballots like this
                self.index = 0                # current ranking
                self.weight = E.V1            # initial weight
                self.residual = E.V0          # untransferable weight
                #
                #  fast copy of ranking -> self.ranking with duplicate detection
                #  http://www.peterbe.com/plog/uniqifiers-benchmark (see f11)
                #
                #  Note that the speed is no longer necessary, since we're sharing
                #  the ranking tuple across rounds, but it's here as an example
                #  of an interesting technique that might be useful elsewhere.
                #
        #         def dedupe(cids):
        #             seen = set()
        #             for cid in cids:
        #                 if cid in seen:
        #                     raise ValueError('duplicate ranking: %s' % cid)
        #                 seen.add(cid)
        #                 yield cid
        #         self.ranking = tuple(dedupe(ranking)) if ranking else tuple()
        
                #  self.ranking is a tuple of candidate IDs, with a None sentinel at the end
                self.ranking = list()
                for cid in ranking:
                    c = E.candidate(cid)
                    if c in E.eligible:
                        self.ranking.append(c)
                self.ranking = tuple(self.ranking)

        def copy(self):
            "return a copy of this ballot"
            b = Election.Ballot(None)
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
        def topCand(self):
            "return top candidate, or None if exhausted"
            return self.ranking[self.index] if self.index < len(self.ranking) else None
        
        @property
        def vote(self):
            "return total vote of this ballot"
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
        self.cid = cid     # candidate id
        self.order = order # ballot order
        self.name = cname  # candidate name

    #  get/set vote total of this candidate
    #
    def getvote(self):
       "get current vote for candidate"
       return self.E.R.C._vote[self.cid]
    def setvote(self, newvote):
        "set vote for candidate"
        self.E.R.C._vote[self.cid] = newvote
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
       if not self.E.R.C._kf: return None
       return self.E.R.C._kf[self.cid]
    def setkf(self, newkf):
        "set keep factor for candidate"
        self.E.R.C._kf[self.cid] = newkf
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
    hopeful: the set of hopeful candidates
    elected: the set of elected candidates
    defeated: the set of defeated candidates
    withdrawn: access to Election's set of withdrawn candidates
    pending: a (virtual) set of elected candidates pending transfer (WIGM, not Meek)
    isHopeful, etc: boolean test of a single candidate
    nHopeful, etc: number of candidates in set (properties)
    
    
    '''

    def __init__(self, E):
        "create candidate-state object"
        
        self.E = E

        self._vote = dict()   # votes by candidate cid
        self._kf = dict()     # keep factor by candidate cid
        
        self.hopeful = set()
        self.elected = set()
        self.defeated = set()

    @property
    def withdrawn(self):
        "interface to E.withdrawn for consistency"
        return self.E.withdrawn

    @property
    def pending(self):
        "set of elected candidates with transfer pending"
        _pending = set()
        for c in [b.topCand for b in self.E.R.ballots if not b.exhausted and b.topCand in self.elected]:
            _pending.add(c)
        return _pending

    @property
    def hopefulOrElected(self):
        "return union of hopeful and elected candidates"
        return self.hopeful.union(self.elected)

    @property
    def hopefulOrPending(self):
        "return union of hopeful and transfer-pending candidates"
        return self.hopeful.union(self.pending)

    def copy(self):
        "return a copy of ourself"
        C = CandidateState(self.E)
        
        C._vote = self._vote.copy()
        C._kf = self._kf.copy()
        
        C.hopeful = self.hopeful.copy()
        C.elected = self.elected.copy()
        C.defeated = self.defeated.copy()
        return C

    #  add a candidate to the election
    #
    def addCandidate(self, c, isWithdrawn=False):
        "add a candidate"
        if isWithdrawn:
            self.E.withdrawn.add(c)
            self.E.R.log("Add withdrawn: %s" % c.name)
        else:
            self.hopeful.add(c)
            self.E.R.log("Add hopeful: %s" % c.name)

    def elect(self, c, msg='Elect'):
        "elect a candidate; optionally transfer-pending"
        self.hopeful.remove(c)
        self.elected.add(c)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, self.E.V(c.vote)))
    def defeat(self, c, msg='Defeat'):
        "defeat a candidate"
        self.hopeful.remove(c)
        self.defeated.add(c)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, self.E.V(c.vote)))

    def vote(self, c, r=None):
        "return vote for candidate in round r (default=current)"
        if r is None: return self._vote[c.cid]
        return self.E.rounds[r].C._vote[c.cid]

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
