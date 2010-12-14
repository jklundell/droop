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

from __future__ import absolute_import
from .electionmethods import MethodMeek

class Rule(MethodMeek):
    '''
    Rule for counting PR Foundation Meek Reference STV
    http://prfound.org/resources/reference/reference-meek-rule/
    
    Parameters: none

    Meek-PRF enforces these options:
        arithmetic=fixed
        precision=9
        omega=6
    ...and no batch defeats.
    '''
    precision = 9   # fixed-arithmetic precision in digits
    omega10 = 6     # iteration terminator omega = 1/10**omega10
    name = 'meek-prf'

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return cls.name

    @classmethod
    def helps(cls, helps, name):
        "add help string for meek-prf"
        h =  "%s is the PR Foundation's Meek Reference STV.\n" % name
        h += '\nThere are no options.\n'
        h += '  arithmetic: fixed, %d-digit precision\n' % cls.precision
        h += '  omega=%d (iteration limit such that an interation is terminated\n' % cls.precision
        h += '    when surplus < 1/10^omega)\n'
        helps[name] = h
        
    def __init__(self, E):
        "initialize rule"
        self.E = E
        self.omega = None

    def options(self):
        "Meek-PRF forces all relevant options"
        self.E.options.setopt('arithmetic', default='fixed', force=True)
        self.E.options.setopt('precision', default=self.precision, force=True)
        self.E.options.setopt('display', default=self.precision, force=True)
        self.E.options.setopt('omega', default=self.omega10, force=True)

    def info(self):
        "return an info string for the election report"
        return "PR Foundation Meek Reference"

    def tag(self):
        "return a tag string for unit tests"
        return "%s-o%s" % (self.name, self.omega10)

    #########################
    #
    #   Main Election Counter
    #
    #########################
    def count(self):
        "count the election"

        ##  T. Breaking ties
        ##     Ties can arise in B.3, when selecting a candidate for defeat. 
        ##     Use the defined tiebreaking procedure to select for defeat one candidate 
        ##     from the group of tied candidates.

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
            t = C.byTieOrder(tied)[0]
            names =  ", ".join([c.name for c in tied])
            E.logAction('tie', 'Break tie (defeat low candidate): [%s] -> %s' % (names, t))
            return t

        #########################
        #
        #   Initialize Count
        #
        #########################
        E = self.E # election object
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one

        ##  A. Set each candidate to hopeful or withdrawn. 
        ##     Set each hopeful candidate's keep factor kf to 1, 
        ##     and each withdrawn candidate's keep factor to 0.
        ##     Set omega to 0.000001 (1/10^6).

        C = E.C   # candidates
        for c in C.hopeful():
            c.kf = V1    # initialize keep factors
        self.omega = E.V(1) / E.V(10**self.omega10)

        #  Calculate quota and count votes for round-0 reporting
        E.votes = V(E.nBallots)
        E.quota = E.votes / V(E.nSeats+1) + V.epsilon
        for b in E.ballots:
            b.topCand.vote += b.multiplier

        ##  B. Rounds
        ##  B.1. Test count complete. 
        ##       Proceed to step C if all seats are filled, 
        ##       or if the number of elected plus hopeful candidates 
        ##       is less than or equal to the number of seats.

        E.logAction('begin', 'Begin Count')
        while len(C.hopeful()) > E.seatsLeftToFill() > 0:

            E.newRound()    # data structures for new round

            ##  B.2. Iterate.

            iterationStatus = 'iterate'
            lastsurplus = V(E.nBallots)
            while True:

                ##  B.2.a. Distribute votes. 
                ##         For each ballot: set ballot weight w to 1, and then for each candidate, 
                ##         in order of rank on that ballot: 
                ##            add w multiplied by the keep factor kf of the candidate 
                ##            (to 9 decimal places, rounded up) to that candidate's vote v, 
                ##            and reduce w by the same amount, until no further candidate 
                ##            remains on the ballot or until the ballot's weight w is 0.

                for c in (C.hopeful() + C.elected()):
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
                            b.residual -= keep_value      # track residual value of ballot
                            #
                            if b.weight <= V0:
                                break
                    E.residual += b.residual    # track residual for round

                ##  B.2.b. Update quota. 
                ##         Set quota q to the sum of the vote v for all candidates (step B.2a), 
                ##         divided by one more than the number of seats to be filled, 
                ##         truncated to 9 decimal places, plus 0.000000001 (1/109).

                E.votes = sum([c.vote for c in (C.hopeful() + C.elected())], V0)
                E.quota = E.votes // V(E.electionProfile.nSeats+1) + V.epsilon
                
                ##  B.2.c. Find winners. 
                ##         Elect each hopeful candidate with a vote v 
                ##         greater than or equal to the quota (v >= q).

                for c in [c for c in C.hopeful() if c.vote >= E.quota]:
                    c.elect()
                    iterationStatus = 'elected'
                
                ##  B.2.d. Calculate the total surplus s, 
                ##         as the sum of the individual surpluses (v - q) of the elected candidates
                ##         but not less than 0.

                E.surplus = sum([c.vote-E.quota for c in C.elected()], V0)
                if E.surplus < V0:  # unlikely but possible due to precision limits if omega too small
                    E.surplus = V0  # pragma: no cover
                
                ##  B.2.e. Test for iteration finished. 
                ##         If step B.2c elected a candidate, continue at B.1. 
                ##         Otherwise, if the total surplus s is less than omega, 
                ##         or (except for the first iteration) if the total surplus s 
                ##         is greater than or equal to the surplus s in the previous iteration, 
                ##         continue at B.3.

                if iterationStatus != 'elected':
                    if E.surplus < self.omega:
                        iterationStatus = 'omega'
                    elif E.surplus >= lastsurplus:  # pragma: no cover
                        iterationStatus = 'stable'
                        E.log("Stable state detected (%s)" % E.surplus)
                if iterationStatus != 'iterate':
                    break  # iteration complete

                lastsurplus = E.surplus
                    
                ##  B.2.f. Update keep factors. 
                ##         Set the keep factor kf of each elected candidate to the candidate's 
                ##         current keep factor kf, multiplied by the current quota q 
                ##         (to 9 decimal places, rounded up), and then divided by the candidate's 
                ##         current vote v (to 9 decimal places, rounded up). 
                ##         Continue iteration at step B.2a.

                for c in C.elected():
                    c.kf = V.div(V.mul(c.kf, E.quota, round='up'), c.vote, round='up')

            ##  B.2.e. (end of round if iteration resulted in an election)

            if iterationStatus == 'elected':
                continue

            ##  B.3. Defeat low candidate. 
            ##       Defeat the hopeful candidate c with the lowest vote v, 
            ##       breaking any tie per procedure T, 
            ##       where each candidate c' is tied with c if vote v' for c' 
            ##       is less than or equal to v plus total surplus s.
            ##       Set the keep factor kf of c to 0.

            if C.hopeful():
                low_vote = V.min([c.vote for c in C.hopeful()])
                low_candidates = [c for c in C.hopeful() if (low_vote + E.surplus) >= c.vote]
                low_candidate = breakTie(E, low_candidates)
                if iterationStatus == 'omega':
                    low_candidate.defeat(msg='Defeat (surplus %s < omega)' % E.surplus)
                else:  # pragma: no cover
                    low_candidate.defeat(msg='Defeat (stable surplus %s)' % E.surplus)
                low_candidate.vote = V0
                low_candidate.kf = V0

            ##  B.4. Continue. Proceed to the next round at step B.1.            

        ##  C. Count Complete

        for c in C.hopeful():

            ##  C.1. Elect remaining. 
            ##       If any seats are unfilled, elect remaining hopeful candidates.

            if len(C.elected()) < E.electionProfile.nSeats:
                c.elect(msg='Elect remaining')

            ##  C.2. Defeat remaining. 
            ##       Otherwise defeat remaining hopeful candidates.

            else:
                c.defeat(msg='Defeat remaining')
                c.kf = V0
                c.vote = V0

        #  final vote count for reporting
        E.votes = sum([c.vote for c in C.elected()], V0)
        E.residual = V(E.nBallots) - E.votes
