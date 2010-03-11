'''
Generic Election Support
'''

from candidate import Candidate, CandidateState
from value import Value

class Election(object):
    '''
    container for an election
    '''
    rule = None      # election rule class
    V = None         # arithmetic method
    profile = None   # election profile
    rounds = None    # election rounds
    R0 = None        # round 0 (initial state)
    R = None         # current round
    cName = dict()   # candidate names
    candidates = dict()
    withdrawn = set()
    
    def __init__(self, rule, precision=None, guard=None):
        "create an election"

        self.rule = rule
        #
        #  initialize arithmetic
        #
        self.V = Value.ArithmeticClass(precision, guard)
        self.rounds = [self.Round(self)]
        self.R0 = self.R = self.rounds[0]

    def newRound(self):
       "add a round"
       self.rounds.append(self.Round(self))
       self.R = self.rounds[-1]
       self.R.prior = self.rounds[-2]
       return self.R

    def report(self):
        "report election by round"
        s = "Election: %s\n\n" % self.profile.title
        s += "\tRule: %s\n" % self.rule.info(self)
        s += "\tArithmetic: %s\n\n" % self.V.info()
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

    def addCandidate(self, cid, cname, isWithdrawn):
        "add a candidate to the election"
        c = Candidate(self, cid)
        assert cid not in self.candidates, 'duplicate candidate'
        self.candidates[cid] = c
        self.cName[cid] = cname
        self.R0.C.addCandidate(c, msg=None, isWithdrawn=isWithdrawn)
        return c

    def candidateByCid(self, cid):
        "look up candidate by cid"
        return self.candidates[cid]

    class Round(object):
        "one election round"
        
        def __init__(self, e):
            "create a round"
            if not e.R0:
                #
                #  create round 0: the initial state
                #  quota & ballots are filled in later
                #
                self.n = 0
                self.C = CandidateState(e)
                self.quota = None
                self.ballots = None
            else:
                #
                #  subsequent rounds are copies,
                #  so we can look back at previous rounds
                #
                #  e.R and e.C are the current round and candidate states
                #
                previous = e.R
                self.n = previous.n + 1
                self.C = previous.C.copy()
                self.quota = previous.quota
                self.ballots = [b.copy() for b in previous.ballots]
            self.residual = e.V(0)
            self.vote = e.V(0)
            self._log = [] # list of log messages
    
        def advance(self, c):
            "advance ballots with candidate c at top"
            for b in [b for b in self.ballots if b.top == c]:
                b.advance(self.C.hopeful)
    
        def log(self, msg):
            "log a message"
            self._log.append(msg)
            
        def report(self, e):
            "report a round"
            saveR, e.R = e.R, self # provide reporting context
            s = ''
            for line in self._log:
                s += '\t%s\n' % line
            if self._log:
                s += '\t...\n'
            s += '\tHopeful: %s\n' % (" ".join(sorted([c.name for c in self.C.hopeful])) or 'None')
            s += '\tElected: %s\n' % (" ".join(sorted([c.name for c in self.C.elected])) or 'None')
            s += '\tDefeated: %s\n' % (" ".join(sorted([c.name for c in self.C.defeated])) or 'None')
            nontransferable = e.V(0)
            for b in [b for b in self.ballots if b.exhausted]:
                nontransferable = nontransferable + b.vote
            if nontransferable:
                s += '\tNontransferable votes: %s\n' % nontransferable
            if e.R.n == 0 or e.R.prior.quota != e.R.quota:
                s += '\tQuota: %s\n' % e.R.quota
            e.R = saveR
            return s
            
        def dump(self, e):
            "dump a round"

            saveR, e.R = e.R, self # provide reporting context
            s = ''
            
            candidates = sorted([e.candidates[k] for k in e.candidates.keys()], key=lambda c:int(c.cid))
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
            e.R = saveR
            return s
