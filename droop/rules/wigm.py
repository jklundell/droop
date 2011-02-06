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

from __future__ import absolute_import
from .electionmethods import MethodWIGM

class Rule(MethodWIGM):
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
        self.integer_quota = None
        self.defeat_batch = None

    def options(self):
        "initialize election parameters"

        options = self.E.options

        #  set defaults
        #
        if options.setopt('arithmetic', default='guarded') == 'guarded':
            options.setopt('precision', default=18)
            options.setopt('guard', default=options.getopt('precision')//2)
        elif options.getopt('arithmetic') == 'fixed':
            options.setopt('precision', default=9)

        #  integer_quota: use Droop quota rounded up to whole number
        #  defeat_batch=zero: defeat all hopeful candidates with zero votes after first surplus transfer
        #
        self.integer_quota = options.setopt('integer_quota', default=False, allowed=(True, False))
        self.defeat_batch = options.setopt('defeat_batch', default='none', allowed=('none', 'zero'))
    
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
        def hasQuota(candidate):
            '''
            Determine whether a candidate has a quota.
            
            If using exact arithmetic, then: vote > quota
            Otherwise: vote >= quota, since quota has been rounded up
            '''
            if E.V.exact:
                return candidate.vote > E.quota
            return candidate.vote >= E.quota
    
        def calcQuota():
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
            if ballot.exhausted:
                E.exhausted += ballot.vote
            else:
                ballot.topCand.vote += ballot.vote

        def breakTie(E, tied, reason=None):
            '''
            break a tie
            
            reason must be 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to defeat. 
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
        E.quota = calcQuota()

        #  Calculate initial vote totals
        #
        for b in E.ballots:
            b.topCand.vote += b.vote
        E.exhausted = V0  # track non-transferable votes

        E.logAction('begin', 'Begin Count')
        while len(C.hopeful()) > E.seatsLeftToFill() > 0:
            E.newRound()

            #  elect new winners
            #
            for c in [c for c in C.hopeful(order='vote', reverse=True) if hasQuota(c)]:
                c.elect(pending=True)      # elect with transfer pending

            #  find & transfer highest surplus
            #
            if C.pending():
                high_vote = max(c.vote for c in C.pending())
                high_candidates = [c for c in C.pending() if c.vote == high_vote]
                high_candidate = breakTie(E, high_candidates, 'surplus')
                high_candidate.unpend('Transfer high surplus')
                surplus = high_candidate.vote - E.quota
                for b in (b for b in E.ballots if b.topRank == high_candidate.cid):
                    b.weight = (b.weight * surplus) / high_candidate.vote
                    transfer(b)
                high_candidate.vote = E.quota
                E.logAction('transfer', "Surplus transferred: %s (%s)" % (high_candidate, surplus))

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
                        transfer(b)
                    c.vote = V0
                    E.logAction('transfer', "Transfer defeated: %s" % c)

        #  Election over.
        #  Elect any pending candidates
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.pending():
            c.unpend()
        for c in C.hopeful():
            if len(C.elected()) < E.nSeats:
                c.elect(msg='Elect remaining')
            else:
                c.defeat(msg='Defeat remaining')
