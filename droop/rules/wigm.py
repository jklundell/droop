'''
Count election using Generic WIGM STV

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

from electionrule import ElectionRule
from droop.common import UsageError

class Rule(ElectionRule):
    '''
    Rule for counting Generic WIGM elections
    
    Options: arithmetic type, integer_quota, defeat_batch
    '''
    method = 'wigm' # underlying method
    name = 'wigm'
    
    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return cls.name

    @classmethod
    def helps(cls, helps, name):
        "create help string for wigm"
        h =  '%s implements the Weighted Inclusive Gregory Method.\n' % name
        h += '\noptions:\n'
        h += '  (qx*, rational, fixed, integer): arithmetic\n'
        h += '  integer_quota=(false*, true): round quota up to next integer\n'
        h += '  defeat_batch=(none*, zero): after surplus transfer, defeat candidates with no first choices\n'
        h += '    *default\n'
        helps[name] = h
        
    def __init__(self, E):
        "initialize rule"
        self.E = E

    def options(self, options=dict(), used=set(), ignored=set()):
        "initialize election parameters"
        
        #  set defaults
        #
        if options.setdefault('arithmetic', 'guarded') == 'guarded':
            options.setdefault('precision', 18)
            options.setdefault('guard', options['precision']//2)
        elif options['arithmetic'] == 'fixed':
            options.setdefault('precision', 9)

        #  integer_quota: use Droop quota rounded up to whole number
        #  defeat_batch=zero: defeat all hopeful candidates with zero votes after first surplus transfer
        #
        self.integer_quota = options.get('integer_quota', False)
        if self.integer_quota not in (True, False):
            raise UsageError('%s: integer_quota=%s; must be True or False' % (self.name, self.integer_quota))
        self.defeat_batch = options.get('defeat_batch', 'none')
        if self.defeat_batch not in ('none', 'zero'):
            raise UsageError('%s: defeat_batch=%s; must be "none" or "zero"' % (self.name, self.defeat_batch))

        used |= set(('arithmetic', 'precision', 'guard', 'display', 'integer_quota', 'defeat_batch'))
        return options
    
    def info(self):
        "return an info string for the election report"
        return "Generic Weighted Inclusive Gregory Method (WIGM)"

    def tag(self):
        "return a tag string for unit tests"
        return self.name

    #########################
    #
    #   Main Election Counter
    #
    #########################
    def count(self):
        "count the election"
        
        #  local support functions
        #
        def hasQuota(E, candidate):
            '''
            Determine whether a candidate has a quota.
            
            If using exact arithmetic, then: vote > quota
            Otherwise: vote >= quota, since quota has been rounded up
            '''
            if E.V.exact:
                return candidate.vote > E.quota
            return candidate.vote >= E.quota
    
        def calcQuota(E):
            '''
            Calculate quota.
            
            Round up if not using exact arithmetic.
            '''
            if self.integer_quota:
                return V(1 + E.nBallots // (E.nSeats+1))
            if V.exact:
                return V(E.nBallots) / V(E.nSeats+1)
            return V(E.nBallots) / V(E.nSeats+1) + V.epsilon
        
        def transfer(ballot):
            '''
            Transfer ballot to next hopeful candidate.
            '''
            while not ballot.exhausted and ballot.topCand not in C.hopeful():
                ballot.advance()
            return not ballot.exhausted

        def breakTie(E, tied, reason=None, strong=True):
            '''
            break a tie
            
            purpose must be 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to defeat. 
            
            Set strong to False to indicate that weak tiebreaking should be
            attempted, if relevant. Otherwise the tie is treated as strong.
            
            Not all tiebreaking methods will care about 'purpose' or 'strength',
            but the requirement is enforced for consistency of interface.
            '''
            if len(tied) == 1:
                return tied.pop()
            t = C.byTieOrder(tied)[0]
            names = ", ".join([c.name for c in tied])
            E.logAction('tie', 'Break tie (%s): [%s] -> %s' % (reason, names, t.name))
            return t

        #  Local variables for convenience
        #
        E = self.E  # election object
        C = E.C     # candidates
        V = E.V     # arithmetic value class
        V0 = E.V0   # constant zero
        
        #  calculate quota
        #
        E.quota = calcQuota(E)

        #  Calculate initial vote totals
        #
        for b in E.ballots:
            b.topCand.vote += b.vote

        E.logAction('begin', 'Begin Count')
        while len(C.hopeful()) > E.seatsLeftToFill() > 0:
            E.newRound()

            #  elect new winners
            #
            for c in [c for c in C.hopeful(order="vote", reverse=True) if hasQuota(E, c)]:
                c.pend()      # elect with transfer pending

            #  find & transfer highest surplus
            #
            if C.pending():
                high_vote = max(c.vote for c in C.pending())
                high_candidates = [c for c in C.pending() if c.vote == high_vote]
                high_candidate = breakTie(E, high_candidates, 'surplus')
                high_candidate.elect('Transfer high surplus')
                surplus = high_candidate.vote - E.quota
                for b in (b for b in E.ballots if b.topRank == high_candidate.cid):
                    b.weight = (b.weight * surplus) / high_candidate.vote
                    if transfer(b):
                        b.topCand.vote += b.vote
                high_candidate.vote = E.quota
                E.logAction('transfer', "Surplus transferred: %s (%s)" % (high_candidate, V(surplus)))

            #  if no surplus to transfer, defeat a candidate
            #
            elif C.hopeful():
                #  find & defeat candidate with lowest vote
                #
                low_vote = min(c.vote for c in C.hopeful())
                low_candidates = [c for c in C.hopeful() if c.vote == low_vote]
                if low_vote == V0 and self.defeat_batch == 'zero':
                    for c in low_candidates:
                        c.defeat(msg='Defeat batch(zero)')
                else:
                    low_candidate = breakTie(E, low_candidates, 'defeat')
                    low_candidate.defeat()
                    low_candidates = [low_candidate]
                for c in low_candidates:
                    for b in (b for b in E.ballots if b.topRank == c.cid):
                        if transfer(b):
                            b.topCand.vote += b.vote
                    c.vote = V0
                    E.logAction('transfer', "Transfer defeated: %s" % c)

        #  Election over.
        #  Elect any pending candidates
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.pending():
            c.elect(msg='Elect pending')
        for c in C.hopeful():
            if len(C.elected()) < E.nSeats:
                c.elect(msg='Elect remaining')
            else:
                c.defeat(msg='Defeat remaining')
