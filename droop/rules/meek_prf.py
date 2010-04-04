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
        return 'prf-meek-basic'

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
    def tag(cls):
        "return a tag string for unit tests"
        return "prf-meek-basic"

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
        
        #  T. Break tie.
        #
        def breakTie(E, tied):
            '''
            break a tie for defeating low candidate
            
            the tiebreaking method: candidates are randomly ordered,
            and the order of entry in the ballot file 
            or the profile =tie order is the tiebreaking order:
            choose the first candidate in that order.
            '''
            if len(tied) == 1:
                return tied[0]
            tied = CS.sortByTieOrder(tied)
            t = tied[0]
            R.log('Break tie (defeat low candidate): [%s] -> %s' % (", ".join([c.name for c in tied]), t.name))
            return t

        #########################
        #
        #   Initialize Count
        #
        #########################
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one
        R = E.R0

        #  A. initialize omega: 1/10^6
        #     initialize quota
        #     set hopeful keep factors to 1
        #     set withdrawn keep factors to 0
        #
        #     count votes for reporting purposes
        #
        cls._omega = V(1) / V(10**cls.omega)

        R.votes = V(E.nBallots)
        R.quota = R.votes / V(E.nSeats+1) + V.epsilon
        CS = R.CS   # candidate state
        for c in E.withdrawn:
            c.kf = V0
        for c in CS.hopeful:
            c.kf = V1    # initialize keep factors
            c.vote = V0  # initialize round-0 vote
        for b in R.ballots:
            if b.topCand:
                b.topCand.vote += V(b.multiplier)  # count first-place votes for round 0 reporting

        #  B. next round
        #  B.1. test count complete
        #
        while CS.nHopeful > E.seatsLeftToFill() > 0:

            R = E.newRound()    # data structures for new round
            CS = R.CS           # candidate state

            #  B.2. iterate
            #       next round if iteration elected a candidate
            #
            iterationStatus = 'iterate'
            lastsurplus = V(E.nBallots)
            while True:
                #
                #  B.2.a
                #  distribute vote for each ballot
                #  and add up vote for each candidate
                #
                for c in CS.hopefulOrElected:
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
                        kw = V.mul(b.weight, c.kf, round='up')  # keep-weight
                        kv = kw * b.multiplier  # keep-value
                        c.vote += kv            # credit keep-value to candidate
                        b.weight -= kw          # reduce ballot weight
                        b.residual -= kv        # residual value of ballot
                        #
                        if b.weight <= V0:
                            break
                    R.residual += b.residual    # residual for round


                #  B.2.b. update quota
                #
                R.votes = sum([c.vote for c in CS.hopefulOrElected], V0)
                R.quota = R.votes / V(E.electionProfile.nSeats+1) + V.epsilon
                
                #  B.2.c. find winners
                #
                for c in [c for c in CS.sortByOrder(CS.hopeful) if c.vote >= R.quota]:
                    CS.elect(c)
                    iterationStatus = 'elected'
                
                #  B.2.d. calculate total surplus
                #
                R.surplus = sum([c.vote-R.quota for c in CS.elected], V0)
                
                #  B.2.e. test iteration complete
                #
                if iterationStatus == 'elected':
                    break
                if R.surplus < Rule._omega:
                    iterationStatus = 'omega'
                if R.surplus >= lastsurplus:
                    R.log("Stable state detected (%s)" % R.surplus)
                    iterationStatus = 'stable'
                if iterationStatus != 'iterate':
                    break  # iteration complete

                lastsurplus = R.surplus
                    
                #  B.2.f. update keep factors
                #
                for c in CS.elected:
                    c.kf = V.div(V.mul(c.kf, R.quota, round='up'), c.vote, round='up')

            #  B.3. end of round if iteration resulted in an election
            #
            if iterationStatus == 'elected':
                continue

            #  B.4. defeat candidate with lowest vote
            #
            #  find candidate(s) within surplus of lowest vote (effectively tied)
            #
            low_vote = V.min([c.vote for c in CS.hopeful])
            low_candidates = [c for c in CS.hopeful if (low_vote + R.surplus) >= c.vote]
            
            #  defeat candidate with lowest vote, breaking tie if necessary
            #
            if low_candidates:
                low_candidate = breakTie(E, low_candidates)
                if iterationStatus == 'omega':
                    CS.defeat(low_candidate, msg='Defeat (surplus %s < omega)' % V(R.surplus))
                else:
                    CS.defeat(low_candidate, msg='Defeat (stable surplus %s)' % V(R.surplus))
                low_candidate.kf = V0
                low_candidate.vote = V0
            #
            #  B.5 continue at B.1.
        
        #  C. Elect or defeat remaining hopeful candidates
        #
        for c in CS.sortByOrder(CS.hopeful):
            if CS.nElected < E.electionProfile.nSeats:
                CS.elect(c, msg='Elect remaining')
            else:
                CS.defeat(c, msg='Defeat remaining')
                c.kf = V0
                c.vote = V0
