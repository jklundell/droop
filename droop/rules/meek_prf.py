'''
Count election using PR Foundation Meek Reference STV

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
    Rule for counting PR Foundation Meek Reference STV
    
    Parameters: none

    Meek-PRF is equivalent to the generalized Meek rule with the following options:
        arithmetic=fixed
        precision=9
        omega=6
    ...and no batch defeats.
    '''
    
    precision = 9  # fixed-arithmetic precision in digits
    omega = 6      # iteration terminator

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return 'meek-prf'

    @classmethod
    def helps(cls, helps, name):
        "add help string for meek-prf"
        h =  "%s is the PR Foundation's Meek Reference STV.\n" % name
        h += '\nThere are no options.\n'
        h += '  arithmetic: fixed, %d-digit precision\n' % cls.precision
        h += '  omega=%d (iteration limit such that an interation is terminated\n' % cls.omega
        h += '    when surplus < 1/10^omega)\n'
        helps[name] = h
        
    @classmethod
    def options(cls, options=dict()):
        "override options"
        
        options['arithmetic'] = 'fixed'       # fixed-point arithmetic
        options['precision'] = cls.precision  # digits of precision
        options['omega'] = cls.omega          # test: surplus < 1/10^omega
        return options

    @classmethod
    def info(cls):
        "return an info string for the election report"
        return "PR Foundation Meek Reference"

    @classmethod
    def reportMode(cls):
        "how should this election be reported? meek or wigm"
        return 'meek'

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
        def countComplete():
            "test for end of count"
            return C.nHopeful <= E.seatsLeftToFill() or E.seatsLeftToFill() <= 0

        def hasQuota(E, candidate):
            "Determine whether a candidate has a quota (ie, is elected)."
            return candidate.vote >= E.R.quota
    
        def calcQuota(E):
            "Calculate quota."
            return E.R.votes / E.V(E.electionProfile.nSeats+1) + E.V.epsilon
    
        def breakTie(E, tied, purpose=None):
            '''
            break a tie
            
            purpose is 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to eliminate. 
            
            the tiebreaking method: candidates are randomly ordered,
            and the order of entry in the ballot file is the tiebreaking order:
            choose the first candidate in that order.
            '''
            assert purpose in ('surplus', 'elect', 'defeat')
            if not tied:
                return None
            if len(tied) == 1:
                return tied[0]
            t = C.sortByOrder(tied)[0]
            R.log('Break tie (%s): [%s] -> %s' % (purpose, ", ".join([c.name for c in tied]), t.name))
            return t

        #  iterateStatus constants
        #
        IS_none = None
        IS_omega = 1      # iteration stopped because surplus < omega
        IS_elected = 2    # iteration stopped because candidate(s) elected
        IS_stable = 3     # iteration stopped because surplus reached stable value

        def iterate():
            "Iterate until surplus is sufficiently low"
            iStatus = IS_none
            lastsurplus = V(E.nBallots)
            while True:
                #
                #  distribute vote for each ballot
                #  and add up vote for each candidate
                #
                for c in C.hopefulOrElected:
                    c.vote = V0
                R.residual = V0
                for b in R.ballots:
                    b.weight = V1
                    b.residual = V(b.multiplier)
                    for c in b.ranking:
                        #
                        #  distribute surpluses
                        #
                        #  kv = w*kf rounded up * m     keep vote
                        #  w -= w*kf rounded up         new weight
                        # 
                        kw = V.mul(b.weight, c.kf, round='up')  # keep weight
                        kv = kw * b.multiplier
                        c.vote += kv
                        b.weight -= kw
                        b.residual -= kv  # residual value of ballot
                        #
                        if b.weight <= V0:
                            break
                    R.residual += b.residual     # residual for round

                R.votes = sum([c.vote for c in C.hopefulOrElected], V0)

                #  D.3. update quota
                #
                R.quota = calcQuota(E)
                
                #  D.4. find winners
                #
                for c in [c for c in C.hopeful if hasQuota(E, c)]:
                    C.elect(c)
                    iStatus = IS_elected
                
                #  D.6. calculate total surplus
                #
                R.surplus = sum([c.vote-R.quota for c in C.elected], V0)
                
                #  D.7. test iteration complete
                #
                if iStatus == IS_elected:
                    return IS_elected
    
                if R.surplus < Rule._omega:
                    return IS_omega
                if R.surplus >= lastsurplus:
                    R.log("Stable state detected (%s)" % R.surplus)
                    return IS_stable
                lastsurplus = R.surplus
                    
                #  D.8. update keep factors
                #
                for c in C.elected:
                    c.kf = V.div(V.mul(c.kf, R.quota, round='up'), c.vote, round='up')
            
        #########################
        #
        #   Initialize Count
        #
        #########################
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one

        #  set _omega: 1/10**omega
        #
        cls._omega = V(1) / V(10**cls.omega)

        E.R0.votes = V(E.electionProfile.nBallots)
        E.R0.quota = calcQuota(E)
        R = E.R0
        C = R.C   # candidate state
        for c in E.withdrawn:
            c.kf = V0
        for c in C.hopeful:
            c.kf = V1    # initialize keep factors
            c.vote = V0  # initialize round-0 vote
        for b in R.ballots:
            if b.topCand:
                b.topCand.vote += V(b.multiplier)  # count first-place votes for round 0 reporting

        while not countComplete():

            #  B. next round
            #
            R = E.newRound()
            C = R.C   # candidate state

            #  C. iterate
            #     next round if iteration elected a candidate
            #
            iterationStatus = iterate()
            if iterationStatus == IS_elected:
                continue

            #  D. defeat candidate with lowest vote
            #
            #  find candidate(s) within surplus of lowest vote (effectively tied)
            #
            low_vote = V.min(c.vote for c in C.hopeful)
            low_candidates = [c for c in C.hopeful if (low_vote + R.surplus) >= c.vote]
            
            #  defeat candidate with lowest vote, breaking tie if necessary
            #
            if low_candidates:
                low_candidate = breakTie(E, low_candidates, 'defeat')
                if iterationStatus == IS_omega:
                    C.defeat(low_candidate, msg='Defeat (surplus %s < omega)' % V(R.surplus))
                else:
                    C.defeat(low_candidate, msg='Defeat (stable surplus %s)' % V(R.surplus))
                low_candidate.kf = V0
                low_candidate.vote = V0
        
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful.copy():
            if C.nElected < E.electionProfile.nSeats:
                C.elect(c, msg='Elect remaining')
            else:
                C.defeat(c, msg='Defeat remaining')
                c.kf = V0
                c.vote = V0
