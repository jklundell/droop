'''
Count election using Reference WIGM STV

copyright 2010 by Jonathan Lundell
'''

import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))
from modules.value import Value

class Rule:
    '''
    Rule for counting Model WIGM elections
    
    Parameter: arithmetic type
    '''
    
    @classmethod
    def initialize(cls, E, options=dict()):
        "initialize election parameters"
        
        #  set defaults
        #
        if not options.get('arithmetic'):
            options['arithmetic'] = 'quasi-exact'

        #  initialize and return arithmetic
        #
        return Value.ArithmeticClass(options)

    @classmethod
    def info(cls):
        "return an info string for the election report"
        return "Model Weighted Inclusive Gregory Method (WIGM)"

    @classmethod
    def reportMode(cls):
        "how should this election be reported? meek or wigm"
        return 'wigm'

    #########################
    #
    #   Main Election Counter
    #
    #########################
    @classmethod
    def count(cls, E):
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
                return candidate.vote > E.R.quota
            return candidate.vote >= E.R.quota
    
        def calcQuota(E):
            '''
            Calculate quota.
            
            Round up if not using exact arithmetic.
            '''
            if V.exact:
                return V(E.nBallots) / V(E.nSeats+1)
            return V(E.nBallots) / V(E.nSeats+1) + V.epsilon
        
        def breakTie(E, tied, purpose=None, strong=True):
            '''
            break a tie
            
            purpose must be 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to eliminate. 
            
            Set strong to False to indicate that weak tiebreaking should be
            attempted, if relevant. Otherwise the tie is treated as strong.
            
            Not all tiebreaking methods will care about 'purpose' or 'strength',
            but the requirement is enforced for consistency of interface.
            '''
            assert purpose in ('surplus', 'elect', 'defeat')
            if not tied:
                return None
            if len(tied) == 1:
                return tied[0]
            if len(tied) > 1:
                tied = C.sortByOrder(tied) # sort by ballot order before making choice
                t = tied[0]  # TODO: real tiebreaker
                s = 'Break tie (%s): [' % purpose
                s += ", ".join([c.name for c in tied])
                s += '] -> %s' % t.name
                E.R.log(s)
                return t

        #  Calculate quota
        #
        E.R0.quota = calcQuota(E)
        R = E.R0  # current round
        C = R.C   # candidate state
        V = E.V   # arithmetic value class
        V0 = E.V0 # constant zero
        
        #  Count votes in round 0 for reporting purposes
        #
        for c in C.hopeful:
            c.vote = V0
        for b in [b for b in R.ballots if not b.exhausted]:
            b.topCand.vote = b.topCand.vote + b.vote

        while C.nHopefulOrElected > E.nSeats and \
               C.nElected < E.nSeats:
            R = E.newRound()
            C = R.C   # candidate state

            #  count votes for hopeful or pending-transfer candidates
            #
            for c in C.hopefulOrPending:
                c.vote = V0
            for b in [b for b in R.ballots if not b.exhausted]:
                b.topCand.vote = b.topCand.vote + b.vote

            #  elect new winners
            #
            for c in [c for c in C.hopeful if hasQuota(E, c)]:
                C.elect(c)                # elect; transfer pending
                if c.vote == R.quota:     # handle new winners with no surplus
                    R.transfer(c)
        
            #  find highest surplus
            #
            high_vote = R.quota
            high_candidates = []
            for c in C.elected:
                if c.vote == high_vote:
                    high_candidates.append(c)
                elif c.vote > high_vote:
                    high_vote = c.vote
                    high_candidates = [c]
            
            # transfer highest surplus
            #
            if high_vote > R.quota:
                # transfer surplus
                high_candidate = breakTie(E, high_candidates, 'surplus')
                surplus = high_vote - R.quota
                for b in [b for b in R.ballots if b.topCand == high_candidate]:
                    b.weight = (b.weight * surplus) / high_vote
                R.transfer(high_candidate)
                high_candidate.vote = R.quota

            #  if no surplus to transfer, eliminate a candidate
            #
            else:
                #  find candidate(s) with lowest vote
                #
                low_vote = R.quota
                low_candidates = []
                for c in C.hopeful:
                    if c.vote == low_vote:
                        low_candidates.append(c)
                    elif c.vote < low_vote:
                        low_vote = c.vote
                        low_candidates = [c]

                #  defeat candidate with lowest vote
                #
                if low_candidates:
                    low_candidate = breakTie(E, low_candidates, 'defeat')
                    C.defeat(low_candidate)
                    R.transfer(low_candidate)
        
        #  Election over.
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful.copy():
            if C.nElected < E.nSeats:
                C.elect(c, msg='Elect remaining')
            else:
                C.defeat(c, msg='Defeat remaining')
    

