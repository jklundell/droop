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
from droop.common import UsageError
from droop.election import CandidateSet

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
    
    defaultPrecision = 9  # fixed-arithmetic precision in digits
    defaultOmega = 6      # iteration terminator
    precision = None
    omega = None
    name = 'meek-prf'

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return cls.name

    @classmethod
    def options(cls, options=dict()):
        "override options"
        
        if options.setdefault('arithmetic', 'fixed') != 'fixed':
            raise UsageError('%s does not support %s arithmetic' % (cls.name, options['arithmetic']))
        cls.precision = options.setdefault('precision', cls.defaultPrecision)
        cls.omega = options.setdefault('omega', cls.defaultOmega)
        return options

    @classmethod
    def helps(cls, helps, name):
        "add help string for meek-prf"
        h =  "%s is the PR Foundation's Meek Reference STV.\n" % name
        h += '\nThere are no options.\n'
        h += '  arithmetic: fixed, %d-digit precision\n' % cls.defaultPrecision
        h += '  omega=%d (iteration limit such that an interation is terminated\n' % cls.defaultOmega
        h += '    when surplus < 1/10^omega)\n'
        helps[name] = h
        
    @classmethod
    def info(cls):
        "return an info string for the election report"
        return "PR Foundation Meek Reference"

    @classmethod
    def tag(cls):
        "return a tag string for unit tests"
        return "%s-o%s" % (cls.name, cls.omega)

    @classmethod
    def method(cls):
        "underlying method: meek or wigm"
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
                return tied.pop()
            t = tied.byTieOrder()[0]
            names =  ", ".join([c.name for c in tied])
            E.logAction('tie', 'Break tie (defeat low candidate): [%s] -> %s' % (names, t))
            return t

        #########################
        #
        #   Initialize Count
        #
        #########################
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one

        #  A. initialize omega: 1/10^6
        #     initialize quota
        #     set hopeful keep factors to 1
        #
        #     count votes for reporting purposes
        #
        cls._omega = V(1) / V(10**cls.omega)

        E.votes = V(E.nBallots)
        E.quota = E.votes / V(E.nSeats+1) + V.epsilon
        CS = E.CS   # candidate state
        for c in CS.hopeful:
            c.kf = V1    # initialize keep factors
        for b in E.ballots:
            b.topCand.vote += b.multiplier  # count first-place votes for round 0 reporting

        #  B. next round
        #  B.1. test count complete
        #
        while len(CS.hopeful) > E.seatsLeftToFill() > 0:

            E.newRound()    # data structures for new round

            #  B.3. set vote and keep factor of defeated candidates to 0
            #       Note: we defer this until after the new round is begun so that the
            #             previous-round report contains the vote for the defeated candidate.
            #
            for c in CS.defeated:
                c.vote = V0
                c.kf = V0

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
                for c in (CS.hopeful | CS.elected):
                    c.vote = V0
                E.residual = V0
                for b in E.ballots:
                    b.weight = V1
                    b.residual = b.multiplier
                    for c in (E.candidate(cid) for cid in b.ranking):
                        #
                        #  distribute votes
                        #
                        #  kv = w*kf rounded up * m     keep vote
                        #  w -= w*kf rounded up         new weight
                        # 
                        if c.kf:
                            keep_weight = V.mul(b.weight, c.kf, round='up')
                            keep_value = keep_weight * b.multiplier
                            c.vote += keep_value          # credit keep-value to candidate
                            b.weight -= keep_weight       # reduce ballot weight
                            b.residual -= keep_value      # residual value of ballot
                            #
                            if b.weight <= V0:
                                break
                    E.residual += b.residual    # residual for round

                #  B.2.b. update quota
                #
                E.votes = sum([c.vote for c in (CS.hopeful | CS.elected)], V0)
                E.quota = E.votes / V(E.electionProfile.nSeats+1) + V.epsilon
                
                #  B.2.c. find winners
                #
                for c in [c for c in CS.hopeful if c.vote >= E.quota]:
                    CS.elect(c)
                    iterationStatus = 'elected'
                
                #  B.2.d. calculate total surplus
                #
                E.surplus = sum([c.vote-E.quota for c in CS.elected], V0)
                if E.surplus < V0:  # unlikely but possible due to precision limits if omega too small
                    E.surplus = V0
                
                #  B.2.e. test iteration complete
                #
                if iterationStatus != 'elected':
                    if E.surplus < Rule._omega:
                        iterationStatus = 'omega'
                    elif E.surplus >= lastsurplus:
                        iterationStatus = 'stable'
                        E.log("Stable state detected (%s)" % V(E.surplus))
                if iterationStatus != 'iterate':
                    break  # iteration complete

                lastsurplus = E.surplus
                    
                #  B.2.f. update keep factors
                #
                for c in CS.elected:
                    c.kf = V.div(V.mul(c.kf, E.quota, round='up'), c.vote, round='up')

            #  B.2.e. end of round if iteration resulted in an election
            #
            if iterationStatus == 'elected':
                continue

            #  B.3. defeat candidate with lowest vote
            #
            #  find candidate(s) within surplus of lowest vote (effectively tied)
            #  defeat candidate with lowest vote, breaking tie if necessary
            #
            if CS.hopeful:
                low_vote = V.min([c.vote for c in CS.hopeful])
                low_candidates = CandidateSet([c for c in CS.hopeful if (low_vote + E.surplus) >= c.vote])
                low_candidate = breakTie(E, low_candidates)
                if iterationStatus == 'omega':
                    CS.defeat(low_candidate, msg='Defeat (surplus %s < omega)' % V(E.surplus))
                else:
                    CS.defeat(low_candidate, msg='Defeat (stable surplus %s)' % V(E.surplus))
            #
            #  B.4 continue at B.1.
        
        #  C. Elect or defeat remaining hopeful candidates
        #
        for c in list(CS.hopeful):
            if len(CS.elected) < E.electionProfile.nSeats:
                CS.elect(c, msg='Elect remaining')
            else:
                CS.defeat(c, msg='Defeat remaining')
                c.kf = V0
                c.vote = V0

        #  final vote count for reporting
        E.votes = sum([c.vote for c in CS.elected], V0)
        E.residual = V(E.nBallots) - E.votes

