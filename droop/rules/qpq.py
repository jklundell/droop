'''
Count election using Quota Preferential by Quotient (QPQ)

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


    Quota Preferential by Quotient (QPQ)

    Procedure (from Woodall paper http://www.votingmatters.org.uk/ISSUE17/I17P1.PDF)
    
    2.1.  Set each candidate to hopeful
    2.2.  Each ballot has elected 0 candidates
    Round:
    2.3.  Calculate quotient qc (count) of each hopeful candidate c
          qc = vc/(1+tc)
          where vc is number of ballots ranking C first
          tc is sum of all fractional numbers of candidates those ballots
          have so far elected
    2.4.  Quota Q = va/(1+s-tx)
          where va is number of active ballots (ballots with hopeful candidate(s))
          s is total number of seats to be filled
          tx is sum of fractional number of candidates elected by all inactive ballots
    2.5a. Elect candidate with highest quotient if quotient > quota
          update contribution of ballots contributing to c to 1/qc
    2.5b. If no candidate elected in 5a, exclude hopeful with smallest quotient
    2.6.  Count ends when no hopeful candidates remain
'''

from electionrule import ElectionRule

class Rule(ElectionRule):
    '''
    Rule for counting QPQ
    '''

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return 'qpq'

    @classmethod
    def tag(cls):
        "return a tag string for unit tests"
        return 'qpq'

    @classmethod
    def options(cls, options=dict()):
        "initialize election parameters"

        #  initialize and return arithmetic
        #
        #  (override arithmetic parameters)
        #
        options['arithmetic'] = 'guarded'
        options['precision'] = 9
        return options

    @classmethod
    def helps(cls, helps, name):
        "create help string for scottish stv"
        h =  'Quota Preferential by Quotient.\n'
        h += '\nThere are no options.\n'
        h += '  arithmetic: guarded\n'
        h += '  precision=9\n'
        helps[name] = h
        
    @classmethod
    def info(cls):
        "return an info string for the election report"
        return "QPQ"
        
    @classmethod
    def method(cls):
        "underlying method: meek, wigm or qpq"
        return 'qpq'

    #########################
    #
    #   Main Election Counter
    #
    #########################
    @classmethod
    def count(cls, E):
        "count the election with QPQ"

        #  local support functions
        #
        def breakTie(tied, reason=None):
            '''
            break a tie by lot
            '''
            if len(tied) == 1:
                return tied[0]
            names = ", ".join([c.name for c in tied])
            tied = CS.sortByTieOrder(tied) # sort by tie-order before making choice
            t = tied[0]                    # break tie by lot
            E.R.log('Break tie by lot (%s): [%s] -> %s' % (reason, names, t.name))
            return t

        def countComplete():
            '''
            test for count complete
            '''
            if E.seatsLeftToFill() <= 0:
                return True
            if CS.nHopeful <= E.seatsLeftToFill():
                return True
            return False

        #########################
        #
        #   COUNT THE ELECTION
        #
        #########################

        R = E.R0  # current round
        CS = R.CS   # candidate state
        V = E.V   # arithmetic value class
        V0 = E.V0 # constant zero
        V1 = E.V1 # constant one

        #  Calculate initial quota
        #
        R.tx = V0
        R.ta = V0
        R.va = V(sum(b.multiplier for b in E.ballots if not b.exhausted))
        R.quota = R.va / V(1 + E.nSeats) - R.tx  # quota [2.4]
        R.votes = V(E.nBallots)

        #  2.2: each ballot has elected 0 candidates
        #
        for b in E.ballots:
            b.weight = V0

        restart = True
        while (not countComplete()):
        
            R = E.newRound()
            CS = R.CS   # candidate state
            if restart:
                restart = False
                for c in list(CS.elected):
                    CS.unelect(c)
                for b in E.ballots:
                    b.restart(V0)
                    b.transfer(CS.hopeful)

            #  2.3. At the start of each stage, the quotients of all the hopeful candidates 
            #  are calculated, as follows. The ballots contributing to a particular hopeful
            #  candidate c are those ballots on which c is the topmost hopeful candidate.
            #  The quotient assigned to c is defined to be qc = vc/(1+tc), where vc is the 
            #  number of ballots contributing to c, and tc is the sum of all the fractional
            #  numbers of candidates that those ballots have so far elected.
            #
            #  2.4. A ballot is active if it includes the name of a hopeful candidate 
            #  (and is a valid ballot), and inactive otherwise. The quota is defined to be 
            #  va/(1 + s - tx), where va is the number of active ballots, s is the total number
            #  of seats to be filled, and tx is the sum of the fractional numbers of candidates
            #  that are deemed to have been elected by all the inactive ballots.
            #
            R.tx = V0
            R.va = V0
            tc = dict()
            for c in CS.hopeful:
                c.vote = V0
                tc[c] = V0
            for b in E.ballots:
                if b.exhausted:
                    R.tx += b.weight * b.multiplier  # candidates elected by inactive ballots
                else:
                    R.va += V1 * b.multiplier
                    tc[b.topCand] += b.weight * b.multiplier
                    b.topCand.vote += V(b.multiplier)  # vc [2.3]

            R.ta = V0  # for reporting
            for c in CS.hopeful:
                c.quotient = c.vote / (V1 + tc[c])
                R.ta += tc[c]
            
            R.quota = R.va / V(1 + E.nSeats) - R.tx  # quota [2.4]

            #  2.5a. If c is the candidate with the highest quotient, and that quotient is greater
            #  than the quota, then c is declared elected. In this case each of the vc ballots
            #  contributing to c is now deemed to have elected 1/qc candidates in total
            #  (regardless of how many candidates it had elected before c's election); no change
            #  is made to the number of candidates elected by other ballots. (Since these vc
            #  ballots collectively had previously elected tc candidates, and they have now
            #  elected vc/qc = 1 + tc candidates, the sum of the fractional numbers of candidates
            #  elected by all voters has increased by 1.) If all s seats have now been filled,
            #  then the count ends; otherwise it proceeds to the next stage, from paragraph 2.3.
            #
            #  2.5b. If no candidate has a quotient greater than the quota, then the candidate with
            #  the smallest quotient is declared excluded. No change is made to the number of 
            #  candidates elected by any ballot. If all but s candidates are now excluded, then all
            #  remaining hopeful candidates are declared elected and the count ends; otherwise the
            #  count proceeds to the next stage, from paragraph 2.3.

            high_quotient = max(c.quotient for c in CS.hopeful)
            if high_quotient > R.quota:
                high_candidates = [c for c in CS.hopeful if c.quotient == high_quotient]
                high_candidate = breakTie(high_candidates, 'largest quotient')
                CS.elect(high_candidate, 'Elect high quotient', high_quotient)
                new_weight = V1 / high_candidate.quotient
                for b in (b for b in E.ballots if b.topCid == high_candidate.cid):
                    b.weight = new_weight
                    b.transfer(CS.hopeful)
                E.log("%s: %s (%s)" % ('Transfer elected', high_candidate.name, high_quotient))
            else:
                low_quotient = min(c.quotient for c in CS.hopeful)
                low_candidates = [c for c in CS.hopeful if c.quotient == low_quotient]
                low_candidate = breakTie(low_candidates, 'smallest quotient')
                CS.defeat(low_candidate, 'Defeat low quotient', low_quotient)
                for b in (b for b in E.ballots if b.topCid == low_candidate.cid):
                    b.transfer(CS.hopeful)
                E.log("%s: %s (%s)" % ('Transfer defeated', low_candidate.name, low_quotient))
                restart = True

        #  Count complete.

        #  Fill any remaining seats
        #
        if CS.nHopeful <= E.seatsLeftToFill():
            for c in list(CS.hopeful):
                CS.elect(c, 'Elect remaining candidates')

        #  Defeat remaining hopeful candidates for reporting purposes
        #
        for c in list(CS.hopeful):
            CS.defeat(c, msg='Defeat remaining candidates')
