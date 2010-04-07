'''
Count election using Minneapolis MN STV rules

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

Minneapolis Code of Ordinances, Title 8.5, Chapter 167
http://library1.municode.com/default-test/DocView/11490/1/107/109
as of 2009-10-02

Ties are to be broken per Minneapolis Charter Chapter 2 Section 12
http://library1.municode.com/default-test/home.htm?infobase=11490&doc_action=whatsnew

Minneapolis STV is a variation on WIGM,
using fixed-point decimal arithmetic with four digits of precision.

Implementation notes:

1. There is a specification error in 167.20(Mathematically impossible to be elected),
where a candidate that could tie with the next highest candidate is erroneously deemed
"impossible to be elected". The implementation uses actual mathematical certainty,
rather than the erroneous specification, and logs a complaint if the condition arises. 
This should be fixed in the ordinance.

2. The tiebreaking rule requires the presence of the City Council. In their absence,
the implementation uses the standard Python random number generator to break ties.
Ideally, there would be a mechanism to accept external tiebreaking input, or the rule
would be changed so that, for example, the City Council would predetermine a tiebreaking
order.

3. 167.70(1)(f) "number of continuing candidates is equal to the number of offices"
should instead have "equal to or less than", and is so implemented.

4. The language at the end of 167.70(1)(f) should be clarified. The "tie between two"
should be "tie between two or more". But the language isn't needed at all, since any
such tie will be broken when the candidates are defeated.

5. The test for count-complete given in 167.70(1)(f) must be performed after the defeat
of certain losers per 167.70(1)(c) to avoid defeating too many candidates and leaving
a seat unfilled. This should be made explicit, since a reasonable interpretation of (f)
is that the test is performed only after defeating the lowest-vote candidate per (e).
'''

import random
from electionrule import ElectionRule

class Rule(ElectionRule):
    '''
    Rule for counting Minneapolis MN STV
    '''

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return 'mpls'

    @classmethod
    def tag(cls):
        "return a tag string for unit tests"
        return 'mpls'

    @classmethod
    def options(cls, options=dict()):
        "initialize election parameters"

        #  initialize and return arithmetic
        #
        #  arithmetic is fixed decimal, four digits of precision
        #  [167.20(Surplus fraction of a vote, Transfer value)]
        #
        #  (override arithmetic parameters)
        #
        options['arithmetic'] = 'fixed'
        options['precision'] = 4
        return options

    @classmethod
    def helps(cls, helps, name):
        "create help string for mpls"
        h =  'Minneapolis STV is a variant on WIGM.\n'
        h += '\nThere are no options.\n'
        h += '  arithmetic: fixed\n'
        h += '  precision=4\n'
        helps[name] = h
        
    @classmethod
    def info(cls):
        "return an info string for the election report"
        return "Minneapolis MN STV"
        
    @classmethod
    def method(cls):
        "underlying method: meek or wigm"
        return 'wigm'

    #########################
    #
    #   Main Election Counter
    #
    #########################
    @classmethod
    def count(cls, E):
        "count the election with Minneapolis STV rules"

        #  local support functions
        #
        def hasQuota(candidate):
            '''
            Determine whether a candidate has a quota. [167.70(1(a,d))]
            '''
            return candidate.vote >= R.quota

        def calcQuota(E):
            '''
            Calculate quota. [167.20(Threshold)]
            '''
            ##  167.20(Threshold) 
            ##  Threshold = (Total votes cast)/(Seats to be elected + 1) +1, 
            ##  with any fractions disregarded. 

            return V(E.nBallots // (E.nSeats + 1) + 1)

        def findCertainLosers(surplus, fixSpec=True):
            '''
            Find the group of candidates that cannot be elected per 167.20
            '''
            ## 167.20. Mathematically impossible to be elected means either: 
            ##         (1) The candidate could never win because his or her current vote total 
            ##             plus all votes that could possibly be transferred to him or her 
            ##             in future rounds (from candidates with fewer votes, tied candidates, 
            ##             and surplus votes) would not be enough to surpass the candidate 
            ##             with the next higher current vote total; or
            ##         (2) The candidate has a lower current vote total than a candidate 
            ##             who is described by (1).

            #  sortedCands = candidates sorted by vote
            #
            sortedCands = CS.sortByVote(CS.hopeful)

            #   copy the sorted candidates list, 
            #   making each entry a list
            #   where each list one or more candidates with the same vote
            #
            group = []
            sortedGroups = []
            groupvote = V0
            for c in sortedCands:
                if c.vote == groupvote:
                    group.append(c)  # add candidate to tied group
                else:
                    if group:
                        sortedGroups.append(group) # save the previous group
                    group = [c]      # start a new group
                    groupvote = c.vote
            if group:
                sortedGroups.append(group)

            #   Scan the groups to find the biggest set of lowest-vote 
            #   'certain-loser' candidates such that:
            #     * we leave enough hopeful candidates to fill the remaining seats
            #     * we don't break up tied groups of candidates
            #     * the total of the surplus and the votes for the defeated batch
            #       is less than the next-higher candidate
            #
            #   We never defeat the last group, because that would mean
            #   defeating all the hopeful candidates, and if that's possible,
            #   the election is already complete and we wouldn't be here.
            #   
            vote = V0
            losers = []
            maybe = []
            maxDefeat = CS.nHopeful - E.seatsLeftToFill() # limit number of defeats
            for g in range(len(sortedGroups) - 1):
                group = sortedGroups[g]
                maybe += group
                #
                #  stop if adding the next higher group would leave too few hopefuls
                #
                if len(maybe) > maxDefeat:
                    break  # too many defeats
                #
                #  vote is all the votes a candidate in this group could get
                #  from hopefuls tied or ranked lower
                #
                vote += group[0].vote * len(group)
                #
                #   stop if vote added to surplus *equals or* surpasses the vote for
                #   a candidate in the next-higher group
                #
                #   167.20 has a mistaken definition of mathematical
                #   impossibility, so log a complaint in the case where 
                #   we deviate from the erroneous specification
                #
                if (vote + surplus) == sortedGroups[g+1][0].vote:
                    names = ", ".join([c.name for c in group])
                    if fixSpec:
                        R.log("Not defeating uncertain loser(s): %s" % names)
                    else:
                        R.log("Defeating uncertain loser(s): %s" % names)
                if (vote + surplus) > sortedGroups[g+1][0].vote:
                    continue
                if fixSpec and (vote + surplus) == sortedGroups[g+1][0].vote:
                    continue
                losers = list(maybe)
            return losers

        def breakTie(tied, reason=None):
            '''
            break a tie by lot [167.70(1)(e)]
            '''
            ##  167.70(f) ...In the case of a tie between two (2) continuing candidates, 
            ##     the tie must be decided by lot as provided in Minneapolis Charter Chapter 2, 
            ##     Section 12, and the candidate chosen by lot must be defeated. 
            ##     The result of the tie resolution must be recorded and reused in the event 
            ##     of a recount.
            ##
            ##     Minneapolis Charter Chapter 2, Section 12. In Case of Tie Vote.
            ##     When two or more candidates for any elective city office shall receive 
            ##     an equal number of votes at the general city election or at a special election, 
            ##     the election shall be determined as between those candidates by 
            ##     the casting of lots in the presence of the City Council 
            ##     at such time and in such manner as the City Council shall direct. 
            ##     (As amended 83-Or-139, Sec 1, 6-10-83; Charter Amend. No. 161, Sec 6, ref. of 11-7-06)

            if len(tied) == 1:
                return tied[0]
            tied = CS.sortByTieOrder(tied) # sort by tie-order before making choice
            t = tied[0]  # in the absence of the City Council...
            names = ", ".join([c.name for c in tied])
            R.log('Break tie (%s): [%s] -> %s' % (reason, names, t.name))
            return t
            
        def countComplete():
            '''
            test for count complete 167.70(1)(f)]
            '''
            ##  f. The procedures in clauses a. to e. must be repeated 
            ##     until the number of candidates whose vote total is equal to or greater than 
            ##     the threshold is equal to the number of seats to be filled, 
            ##     or until the number of continuing candidates is equal to the number of offices 
            ##     yet to be elected. 

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
        random.seed(E.nBallots + E.nSeats) # initialize PRNG

        #  Calculate quota per 167.20(Threshold)
        #
        E.R0.quota = calcQuota(E)
        R.votes = V(E.nBallots)

        #  skip withdrawn candidates
        #
        for c in E.withdrawn:
            R.transfer(c, c.vote, 'Transfer withdrawn')
        
        while True:

            ##  167.70(1)(a)
            ##  a. The number of votes cast for each candidate for the current round 
            ##     must be counted.
            ##
            for c in CS.elected:
                c.vote = R.quota
            for c in CS.hopefulOrPending:
                c.vote = V0
            for b in (b for b in E.ballots if not b.exhausted):
                b.topCand.vote += b.vote

            ##     If the number of candidates whose vote total is equal to or greater than
            ##     the threshold is equal to the number of seats to be filled, 
            ##     those candidates who are continuing candidates are elected 
            ##     and the tabulation is complete. 
            ##

            for c in [c for c in CS.hopeful if hasQuota(c)]:
                CS.elect(c)
            if CS.nElected >= E.nSeats:
                break

            ##     If the number of candidates whose vote total is equal to or greater than
            ##     the threshold is not equal to the number of seats to be filled, 
            ##     a new round begins and the tabulation must continue as described in clause b.

            R = E.newRound()
            CS = R.CS   # candidate state

            ##  167.70(1)(b)
            ##  b. Surplus votes for any candidates whose vote total is equal to 
            ##     or greater than the threshold must be calculated.

            R.surplus = sum([c.surplus for c in CS.elected], V0)

            #  count votes for reporting
            #
            R.votes = sum([c.vote for c in (CS.elected + CS.hopeful)], V0)

            ##  167.70(1)(c)
            ##  c. After any surplus votes are calculated but not yet transferred, 
            ##     all candidates for whom it is mathematically impossible to be elected 
            ##     must be defeated simultaneously. 
            ##     Votes for the defeated candidates must be transferred to each ballot's 
            ##     next-ranked continuing candidate.

            #  fixSpec=True instructs the function to use the correct definition
            #  of mathematical certainty of defeat instead of the erroneous definition
            #  in 167.20.

            certainLosers = findCertainLosers(R.surplus, fixSpec=True)
            for c in CS.sortByOrder(certainLosers):
                CS.defeat(c, 'Defeat certain loser')
                R.transfer(c, c.vote, 'Transfer defeated')

            ##     If no candidate can be defeated mathematically, the tabulation must continue
            ##     as described in clause d. 
            ##     Otherwise, the tabulation must continue as described in clause a.
            
            #   By implication, the test for tabulation-complete given in 167.70(1)(f)
            #   must be performed here; otherwise too many candidates can be defeated.

            if certainLosers:
                if countComplete():
                    break
                continue  ## continue as described in clause a.

            ##  d. The transfer value of each vote cast for an elected candidate 
            ##     must be transferred to the next continuing candidate on that ballot. 
            ##     The candidate with the largest surplus is declared elected and that candidate's
            ##     surplus is transferred. 
            ##     A tie between two (2) or more candidates must immediately and publicly 
            ##     be resolved by lot by the chief election official at the ranked-choice 
            ##     voting tabulation center. 
            ##     The surplus of the candidate chosen by lot must be transferred 
            ##     before other transfers are made. 
            ##     The result of the tie resolution must be recorded and reused in the event 
            ##     of a recount. 
            ##     If no candidate has a surplus, the tabulation must continue 
            ##     as described in clause e. 
            ##     Otherwise, the tabulation must continue as described in clause a.

            #  find candidate(s) with largest surplus
            #
            high_surplus = V0
            high_candidates = []
            for c in CS.pending:
                if c.surplus == high_surplus:
                    high_candidates.append(c)
                elif c.surplus > high_surplus:
                    high_surplus = c.surplus
                    high_candidates = [c]

            # transfer largest surplus
            #
            ## 167.20(Surplus fraction of a vote)
            ##     Surplus fraction of a vote = 
            ##     (Surplus of an elected candidate)/(Total votes cast for elected candidate), 
            ##     calculated to four (4) decimal places, ignoring any remainder. 

            if high_candidates:
                # break tie if required
                high_candidate = breakTie(high_candidates, 'largest surplus')
                for b in (b for b in E.ballots if b.topCand == high_candidate):
                    b.weight = (b.weight * high_surplus) // high_candidate.vote
                R.transfer(high_candidate, high_candidate.surplus, msg='Transfer surplus')
                high_candidate.vote = R.quota
                continue  ## continue as described in clause a.

            ##  e. If there are no transferable surplus votes, 
            ##     the candidate with the fewest votes is defeated. 
            ##     Votes for a defeated candidate are transferred at their transfer value 
            ##     to each ballot's next-ranked continuing candidate. 
            ##     Ties between candidates with the fewest votes must be decided by lot, 
            ##     and the candidate chosen by lot must be defeated. 
            ##     The result of the tie resolution must be recorded and reused 
            ##     in the event of a recount.

            #  find candidate(s) with lowest vote
            #
            low_vote = R.quota
            low_candidates = []
            for c in CS.hopeful:
                if c.vote == low_vote:
                    low_candidates.append(c)
                elif c.vote < low_vote:
                    low_vote = c.vote
                    low_candidates = [c]

            #  defeat candidate with lowest vote
            #
            if low_candidates:
                low_candidate = breakTie(low_candidates, 'defeat low candidate')
                CS.defeat(low_candidate, 'Defeat low candidate')
                R.transfer(low_candidate, low_candidate.vote, msg='Transfer defeated')

            ##  f. The procedures in clauses a. to e. must be repeated 
            ##     until the number of candidates whose vote total is equal to or greater than 
            ##     the threshold is equal to the number of seats to be filled, 
            ##     or until the number of continuing candidates is equal to the number of offices 
            ##     yet to be elected. 

            if countComplete():
                break

            ##     If the number of continuing candidates is equal to the number of offices 
            ##     yet to be elected, any remaining continuing candidates must be declared elected.

            #  Note: implemented as "less than or equal to"
            #
            if CS.nHopeful <= E.seatsLeftToFill():
                for c in list(CS.hopeful):
                    CS.elect(c, 'Elect remaining candidates')
                break

            ##     In the case of a tie between two (2) continuing candidates, 
            ##     the tie must be decided by lot as provided in Minneapolis Charter Chapter 2, 
            ##     Section 12, and the candidate chosen by lot must be defeated. 
            ##     The result of the tie resolution must be recorded and reused in the event 
            ##     of a recount.

            # Note: this will happen, if necessary, at the next defeat-lowest step e above


        #  Tabulation complete.

        ##  f. ...
        ##     If the number of continuing candidates is equal to the number of offices 
        ##     yet to be elected, any remaining continuing candidates must be declared elected.

        #  Note: implemented as "less than or equal to"
        #
        if CS.nHopeful <= E.seatsLeftToFill():
            for c in list(CS.hopeful):
                CS.elect(c, 'Elect remaining candidates')

        #  Defeat remaining hopeful candidates for reporting purposes
        #
        for c in list(CS.hopeful):
            CS.defeat(c, msg='Defeat remaining candidates')
