'''
Generic Election Support

copyright 2010 by Jonathan Lundell
'''

from candidate import Candidate, CandidateState

class Election(object):
    '''
    container for an election
    '''
    rule = None      # election rule class
    V = None         # arithmetic method
    rounds = None    # election rounds
    R0 = None        # round 0 (initial state)
    R = None         # current round
    eligible = set() # all the non-withdrawn candidates
    withdrawn = set()  # all the withdrawn candidates
    _candidates = dict() # candidates by candidate ID
    
    def __init__(self, rule, electionProfile, options=dict()):
        "create an election"

        self.rule = rule # a class
        self.rule.initialize(self, options)
        self.electionProfile = electionProfile

        self.rounds = [self.Round(self)]
        self.R0 = self.R = self.rounds[0]
        for cid in electionProfile.eligible | electionProfile.withdrawn:
            c = Candidate(self, cid, electionProfile.candidateOrder(cid), electionProfile.candidateName(cid))
            assert c.cid not in self._candidates.keys(), 'duplicate candiates (%s)' % c.cid
            self._candidates[cid] = c
            if cid in electionProfile.eligible:
                self.eligible.add(c)
            else:
                self.withdrawn.add(c)
            self.R0.C.addCandidate(c, isWithdrawn=cid in electionProfile.withdrawn)
        for bl in electionProfile.ballotLines:
            self.R0.ballots.append(self.Ballot(self, bl.multiplier, bl.ranking))

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

    def report(self):
        "report election by round"
        s = "\nElection: %s\n\n" % self.title
        s += "\tRule: %s\n" % self.rule.info()
        s += "\tArithmetic: %s\n\n" % self.V.info
        s += self.V.report()
        for round in self.rounds:
            s += "Round %d:\n" % round.n
            s += round.report(self)
        
        #  dump round-by-round details
        #
        s += "\nDump Rounds:\n"
        for round in self.rounds:
            s += round.dump(self)
        return s

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - self.R.C.nElected

    class Round(object):
        "one election round"
        
        def __init__(self, E):
            "create a round"
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
            self.residual = E.V(0)
            self.vote = E.V(0)
            self._log = [] # list of log messages
    
        def transfer(self, c):
            "transfer ballots with candidate c at top"
            for b in [b for b in self.ballots if b.topCand == c]:
                b.transfer(self.C.hopeful)
    
        def log(self, msg):
            "log a message"
            self._log.append(msg)
            
        def report(self, E):
            "report a round"
            saveR, E.R = E.R, self # provide reporting context
            s = ''
            for line in self._log:
                s += '\t%s\n' % line
            if self._log:
                s += '\t...\n'
            s += '\tHopeful: %s\n' % (" ".join(sorted([c.name for c in self.C.hopeful])) or 'None')
            s += '\tElected: %s\n' % (" ".join(sorted([c.name for c in self.C.elected])) or 'None')
            s += '\tDefeated: %s\n' % (" ".join(sorted([c.name for c in self.C.defeated])) or 'None')
            nontransferable = E.V(0)
            for b in [b for b in self.ballots if b.exhausted]:
                nontransferable = nontransferable + b.vote
            if nontransferable:
                s += '\tNontransferable votes: %s\n' % nontransferable
            if E.R.n == 0 or E.R.prior.quota != E.R.quota:
                s += '\tQuota: %s\n' % E.R.quota
            E.R = saveR
            return s
            
        def dump(self, E):
            "dump a round"

            saveR, E.R = E.R, self # provide reporting context
            s = ''
            
            candidates = sorted(E.eligible, key=lambda c:int(c.cid))
            #  if round 0, include a header line
            if self.n == 0:
                h = ['R', 'Q', 'residual']
                for c in candidates:
                    cid = c.cid
                    h += ["'%s.name'" % cid]
                    h += ["'%s.state'" % cid]
                    h += ["'%s.vote'" % cid]
                    h += ["'%s.kf'" % cid]
                h = [str(item) for item in h]
                s += ','.join(h) + '\n'
                
            r = [self.n, self.quota, self.residual]
            for c in candidates:
                cid = c.cid
                r.append(c.name)
                if self.n:
                    r.append('W' if c.isWithdrawn else 'H' if c.isHopeful else 'P' if c.isPending else 'E' if c.isElected else 'D' if c.isDefeated else '?') # state
                    r.append(c.vote)
                    r.append("'-'" if c.kf is None else c.kf)
                else:
                    r.append('W' if c.isWithdrawn else 'H') # state
                    r.append(c.vote) # vote
                    r.append("'-'") # kf
                
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
                self.weight = E.V(1)          # initial weight
                self.residual = E.V(0)        # untransferable weight
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
    
        def transfer(self, hopeful):
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
            
