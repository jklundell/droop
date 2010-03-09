'''
Generic Election Support
'''

from candidate import CandidateState
from value.value import Value

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
    
    def __init__(self, rule, arithmetic=None, precision=None, guard=None):
        "create an election"

        self.rule = rule
        #
        #  initialize arithmetic
        #
        self.V = Value.ArithmeticClass(arithmetic, precision, guard)
        self.rounds = [self.Round(self)]
        self.R0 = self.R = self.rounds[0]

    def newRound(self):
       "add a round"
       self.rounds.append(self.Round(self))
       self.R = self.rounds[-1]
       return self.R

    def report(self):
        "report election by round"
        s = "Election: %s\n\n" % self.profile.title
        s += "\tRule: %s\n" % self.rule.info(self)
        s += "\tArithmetic: %s\n\n" % self.V.info()
        for round in self.rounds:
            s += "Round %d:\n" % round.n
            s += round.report(self)
        return s

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
                self.C = CandidateState()
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
            s += '\tHopeful: %s\n' % (" ".join([c.name for c in self.C.hopeful]) or 'None')
            s += '\tElected: %s\n' % (" ".join([c.name for c in self.C.elected]) or 'None')
            s += '\tDefeated: %s\n' % (" ".join([c.name for c in self.C.defeated]) or 'None')
            nontransferable = e.V(0)
            for b in [b for b in self.ballots if b.exhausted]:
                nontransferable = nontransferable + b.vote
            s += '\tNontransferable votes: %s\n' % nontransferable
            e.R = saveR
            return s
