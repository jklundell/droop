'''
Count election using Reference WIGM STV

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

class Rule(ElectionRule):
    '''
    Rule for counting Model WIGM elections
    
    Parameters: arithmetic type, integer_quota, defeat_batch
    '''
    
    #  options
    #
    integer_quota = False
    defeatBatch = 'none'
    
    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return 'wigm'

    @classmethod
    def helps(cls, helps, name):
        "create help string for wigm"
        h =  'wigm implements the Weighted Inclusive Gregory Method.\n'
        h += '\noptions:\n'
        h += '  (qx*, rational, fixed, integer): arithmetic\n'
        h += '  integer_quota=(false*, true): round quota up to next integer\n'
        h += '  defeat_batch=(none*, zero): after surplus transfer, defeat candidates with no first choices\n'
        h += '    *default\n'
        helps[name] = h
        
    @classmethod
    def options(cls, options=dict()):
        "initialize election parameters"
        
        #  set defaults
        #
        if not options.get('arithmetic'):
            options['arithmetic'] = 'guarded'

        #  integer_quota: use Droop quota rounded up to whole number
        #  defeat_batch=zero: defeat all hopeful candidates with zero votes after first surplus transfer
        #
        cls.integer_quota = options.get('integer_quota', False)
        cls.defeatBatch = options.get('defeat_batch', 'none')

        #  initialize and return arithmetic
        #
        return options
    
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
            if cls.integer_quota:
                return V(1 + E.nBallots // (E.nSeats+1))
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
            if not tied:
                return None
            if len(tied) == 1:
                return tied[0]
            if not tied:
                return None
            if len(tied) == 1:
                return tied[0]
            tied = C.sortByOrder(tied)
            t = tied[0]
            R.log('Break tie (%s): [%s] -> %s' % (purpose, ", ".join([c.name for c in tied]), t.name))
            return t

        #  Calculate quota
        #
        R = E.R0  # current round
        C = R.C   # candidate state
        V = E.V   # arithmetic value class
        V0 = E.V0 # constant zero
        E.R0.quota = calcQuota(E)

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
                    R.transfer(c, c.surplus, msg='Transfer surplus')
        
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
                R.transfer(high_candidate, high_candidate.surplus, msg='Transfer surplus')
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
                    if low_vote == V0 and cls.defeatBatch == 'zero':
                        for c in low_candidates:
                            C.defeat(c, msg='Defeat batch(zero)')
                            R.transfer(c, c.vote, msg='Transfer defeated')
                    else:
                        low_candidate = breakTie(E, low_candidates, 'defeat')
                        C.defeat(low_candidate)
                        R.transfer(low_candidate, low_candidate.vote, msg='Transfer defeated')


        #  Election over.
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful.copy():
            if C.nElected < E.nSeats:
                C.elect(c, msg='Elect remaining')
            else:
                C.defeat(c, msg='Defeat remaining')
    

