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
http://library1.municode.com/default-test/home.htm?infobase=11490
as of 2009-10-02

Ties are to be broken per Minneapolis Charter Chapter 2 Section 12
http://library1.municode.com/default-test/home.htm?infobase=11490

Minneapolis STV is a variation on WIGM,
using fixed-point decimal arithmetic with four digits of precision.

Implementation notes:

1. There is a specification error in 167.20(Mathematically impossible to be elected),
where a candidate that could tie with the next highest candidate is erroneously deemed
"impossible to be elected". The implementation uses actual mathematical certainty,
rather than the erroneous specification, and logs a complaint if the condition arises. 
This should be fixed in the ordinance.

2. The tiebreaking rule requires the presence of the City Council. In their absence,
the implementation uses an external tiebreaking order to break ties.
Ideally, the rule would be changed so that the City Council would predetermine a tiebreaking
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

6. WIGM rules typically elect candidates as soon as they reach a quota. The Minneapolis
rule defer the election of a candidate until that candidate's surplus is to be transferred.
This variation is defensible, even desirable, but because it's a little unusual, the rule
language should make more explicit the implication that votes can be transferred to candidates
who already have a quota but are not yet elected per 167.70(1)(d).


Election Code

The relevant portions of the Minneapolis election code is reproduced below, and is also 
distributed as comments marked with ## in the body of the implementation.


167.20. Definitions. The following words and phrases when used in this chapter shall have the
meanings respectively ascribed to them in this section:

Batch elimination  means a simultaneous defeat of multiple continuing candidates for whom it is
mathematically impossible to be elected.

Chief election official  includes the director of elections and his or her designee.

Continuing candidate  means a candidate who has been neither elected nor defeated.

Duplicate ranking  occurs when a voter ranks the same candidate at multiple rankings for the office
being counted.

Exhausted ballot  means a ballot that cannot be advanced under section 167.60(a)(2) or section
167.70(a)(2).

Highest continuing ranking  means the ranking on a voter's ballot with the lowest numerical value
for a continuing candidate.

Mathematically impossible to be elected  means either: 
   (1) The candidate could never win because his or her current vote total plus all votes that could
   possibly be transferred to him or her in future rounds (from candidates with fewer votes, tied
   candidates, and surplus votes) would not be enough to surpass the candidate with the next higher
   current vote total; or
   (2) The candidate has a lower current vote total than a candidate who is described by (1).

An overvote  occurs when a voter ranks more than one (1) candidate at the same ranking.

Partially defective ballot  means a ballot that is defective to the extent that the election judges
are unable to determine the voter's intent with respect to the office being counted.

Ranked-choice voting  means an election method in which voters rank candidates for an office in
order of their preference and the ballots are counted in rounds that, in the case of a single-seat
election, simulate a series of runoffs until one (1) candidate meets the threshold, or until two (2)
candidates remain and the candidate with the greatest number of votes is declared elected. In the
case of multiple-seat elections, a winning threshold is calculated, and votes, or fractions thereof,
are distributed to candidates according to the preferences marked on each ballot as described in
section 167.70 of this chapter.

Ranked-choice voting tabulation center  means the place selected for the automatic or manual
processing and tabulation of ballots and/or votes.

Ranking  means the number assigned by a voter to a candidate to express the voter's preference for
that candidate. Ranking number one (1) is the highest ranking. A ranking of lower numerical value
indicates a greater preference for a candidate than a ranking of higher numerical value.

Round  means an instance of the sequence of voting tabulation steps established in sections 167.60
and 167.70 of this chapter.

Skipped ranking  occurs when a voter leaves a ranking blank and ranks a candidate at a subsequent
ranking.

Surplus  means the total number of votes cast for an elected candidate in excess of the threshold.

Surplus fraction of a vote  means the proportion of each vote to be transferred when a surplus is
transferred. The surplus fraction is calculated by dividing the surplus by the total votes cast for
the elected candidate, calculated to four (4) decimal places, ignoring any remainder. Surplus
fraction of a vote = (Surplus of an elected candidate)/(Total votes cast for elected candidate),
calculated to four (4) decimal places, ignoring any remainder.

Threshold  means the number of votes sufficient for a candidate to be elected. In any given
election, the threshold equals the total votes counted in the first round after removing partially
defective ballots, divided by the sum of one (1) plus the number of offices to be filled and adding
one (1) to the quotient, disregarding any fractions. Threshold = (Total votes cast)/(Seats to be
elected + 1) +1, with any fractions disregarded.

Transfer value  means the fraction of a vote that a transferred ballot will contribute to the next
ranked continuing candidate on that ballot. The transfer value of a vote cast for an elected
candidate is calculated by multiplying the surplus fraction by its current value, calculated to four
(4) decimal places, ignoring any remainder. The transfer value of a vote cast for a defeated
candidate is the same as its current value.

Transferable vote  means a vote or a fraction of a vote for a candidate who has been either elected
or defeated.

Totally defective ballot  means a ballot that is defective to the extent that the election judges
are unable to determine the voter's intent for any office on the ballot.

An undervote  occurs when a voter does not rank any candidates for an office. (2008-Or-028, 1,
4-18-08; 2009-Or-102, 1, 10-2-09)


167.70. Tabulation of votes, multiple-seat elections. (a) Applicability.  This section applies to a
ranked-choice voting election in which more than one (1) seat in office is to be filled from a
single set of candidates on the ballot. The method of tabulating ranked-choice votes for
multiple-seat elections as described in this section must be known as the "multiple-seat single
transferable vote" method of tabulation.

(1) Tabulation of votes at the ranked-choice voting tabulation center must proceed in rounds for
each office to be counted. The threshold must be calculated and publicly declared. Each round must
proceed sequentially as follows:

   a. The number of votes cast for each candidate for the current round must be counted. If the
   number of candidates whose vote total is equal to or greater than the threshold is equal to the
   number of seats to be filled, those candidates who are continuing candidates are elected and the
   tabulation is complete. If the number of candidates whose vote total is equal to or greater than
   the threshold is not equal to the number of seats to be filled, a new round begins and the
   tabulation must continue as described in clause b.

   b. Surplus votes for any candidates whose vote total is equal to or greater than the threshold
   must be calculated.

   c. After any surplus votes are calculated but not yet transferred, all candidates for whom it is
   mathematically impossible to be elected must be defeated simultaneously. Votes for the defeated
   candidates must be transferred to each ballot's next-ranked continuing candidate. If no candidate
   can be defeated mathematically, the tabulation must continue as described in clause d. Otherwise,
   the tabulation must continue as described in clause a.

   d. The transfer value of each vote cast for an elected candidate must be transferred to the next
   continuing candidate on that ballot. The candidate with the largest surplus is declared elected
   and that candidate's surplus is transferred. A tie between two (2) or more candidates must
   immediately and publicly be resolved by lot by the chief election official at the ranked-choice
   voting tabulation center. The surplus of the candidate chosen by lot must be transferred before
   other transfers are made. The result of the tie resolution must be recorded and reused in the
   event of a recount. If no candidate has a surplus, the tabulation must continue as described in
   clause e. Otherwise, the tabulation must continue as described in clause a.

   e. If there are no transferable surplus votes, the candidate with the fewest votes is defeated.
   Votes for a defeated candidate are transferred at their transfer value to each ballot's
   next-ranked continuing candidate. Ties between candidates with the fewest votes must be decided
   by lot, and the candidate chosen by lot must be defeated. The result of the tie resolution must
   be recorded and reused in the event of a recount.

   f. The procedures in clauses a. to e. must be repeated until the number of candidates whose vote
   total is equal to or greater than the threshold is equal to the number of seats to be filled, or
   until the number of continuing candidates is equal to the number of offices yet to be elected. If
   the number of continuing candidates is equal to the number of offices yet to be elected, any
   remaining continuing candidates must be declared elected. In the case of a tie between two (2)
   continuing candidates, the tie must be decided by lot as provided in Minneapolis Charter Chapter
   2, Section 12, and the candidate chosen by lot must be defeated. The result of the tie resolution
   must be recorded and reused in the event of a recount.

(2) When a single skipped ranking is encountered on a ballot, that ballot shall count towards the
next non-skipped ranking. If any ballot cannot be advanced because no further continuing candidates
are ranked on that ballot, or because a voter has skipped more than one (1) ranking or because an
undervote, overvote, or duplicate ranking is encountered, the ballot shall not count towards any
candidate in that round or in subsequent rounds for the office being counted. (2008-Or-028, 1,
4-18-08; 2009-Or-102, 5, 10-2-09)
'''

from __future__ import absolute_import
from .electionmethods import MethodWIGM

class Rule(MethodWIGM):
    '''
    Rule for counting Minneapolis MN STV
    '''
    method = 'wigm' # underlying method
    name = 'mpls'

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return cls.name

    @classmethod
    def helps(cls, helps, name):
        "create help string for mpls"
        h =  'Minneapolis STV is a variant on WIGM.\n'
        h += '\nThere are no options.\n'
        h += '  arithmetic: fixed\n'
        h += '  precision=4\n'
        helps[name] = h
        
    def __init__(self, E):
        "initialize rule"
        self.E = E

    def options(self):
        "mpls forces all relevant options"

        #  initialize and return arithmetic
        #
        #  arithmetic is fixed decimal, four digits of precision
        #  [167.20(Surplus fraction of a vote, Transfer value)]
        #
        #  (override arithmetic parameters)
        #
        self.E.options.setopt('arithmetic', default='fixed', force=True)
        self.E.options.setopt('precision', default=4, force=True)
        self.E.options.setopt('display', default=4, force=True)

    def info(self):
        "return an info string for the election report"
        return "Minneapolis MN STV"
        
    def tag(self):
        "return a tag string for unit tests"
        return self.name

    #########################
    #
    #   Main Election Counter
    #
    #########################
    def count(self):
        "count the election with Minneapolis STV rules"

        #  local support functions
        #
        def hasQuota(candidate):
            '''
            Determine whether a candidate has a quota. [167.70(1(a,d))]
            '''
            return candidate.vote >= E.quota

        def calcQuota():
            '''
            Calculate quota. [167.20(Threshold)]
            '''
            ##  167.20(Threshold) 
            ##  Threshold = (Total votes cast)/(Seats to be elected + 1) +1, 
            ##  with any fractions disregarded. 

            return V(E.nBallots // (E.nSeats + 1) + 1)

        def transfer(ballot):
            '''
            Transfer ballot to next continuing (hopeful or pending) candidate
            '''
            ##  167.70(1)(d)
            ##  The transfer value of each vote cast for an elected candidate must be transferred
            ##  to the next continuing candidate on that ballot. ...
            ##
            ##  167.70(1)(e)
            ##  ... Votes for a defeated candidate are transferred at their transfer value to each 
            ##  ballot's next-ranked continuing candidate. 
   
            while not ballot.exhausted and ballot.topCand not in (C.hopeful() + C.pending()):
                ballot.advance()
            if ballot.exhausted:
                E.exhausted += ballot.vote
            else:
                ballot.topCand.vote += ballot.vote

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

            #  sortedCands = hopeful candidates below threshold, sorted by vote
            #
            sortedCands = C.hopeful(order='vote')

            #   copy the sorted candidates list to sortedGroups, 
            #   making each entry a list
            #   where each list contains one or more candidates with the same vote
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
            maxDefeat = len(C.hopeful()) - E.seatsLeftToFill() # limit number of defeats
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
                        E.log("Not defeating uncertain loser(s): %s" % names)
                    else:
                        E.log("Defeating uncertain loser(s): %s" % names)  # pragma: no cover
                if (vote + surplus) > sortedGroups[g+1][0].vote:
                    continue
                if fixSpec and (vote + surplus) == sortedGroups[g+1][0].vote:
                    continue
                losers = list(maybe)
            return C.byBallotOrder(losers)

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
                return tied.pop()
            names = ", ".join([c.name for c in tied])
            t = C.byTieOrder(tied)[0]    # sort by tie-order before making choice
            E.logAction('tie', 'Break tie (%s): [%s] -> %s' % (reason, names, t.name))
            return t
            
        #########################
        #
        #   COUNT THE ELECTION
        #
        #########################

        E = self.E
        C = E.C     # candidates
        V = E.V     # arithmetic value class
        V0 = E.V0   # constant zero

        #  Calculate quota per 167.20(Threshold)
        #
        E.quota = calcQuota()

        #  make initial vote count
        #
        ##  167.70(1)(a)
        ##  a. The number of votes cast for each candidate for the current round 
        ##     must be counted.
        ##
        for b in E.ballots:
            b.topCand.vote += b.vote
        E.exhausted = V0    # track non-transferable votes

        E.logAction('begin', 'Begin Count')
        while True:

            ##     If the number of candidates whose vote total is equal to or greater than
            ##     the threshold is equal to the number of seats to be filled, 
            ##     those candidates who are continuing candidates are elected 
            ##     and the tabulation is complete. 
            ##
            for c in [c for c in C.hopeful(order='vote', reverse=True) if hasQuota(c)]:
                c.elect('Candidate at threshold', pending=True)  # election pending
            if len(C.elected()) >= E.nSeats:
                break

            ##     If the number of candidates whose vote total is equal to or greater than
            ##     the threshold is not equal to the number of seats to be filled, 
            ##     a new round begins and the tabulation must continue as described in clause b.

            E.newRound()

            ##  167.70(1)(b)
            ##  b. Surplus votes for any candidates whose vote total is equal to 
            ##     or greater than the threshold must be calculated.
            ##
            E.surplus = sum([c.surplus for c in C.pending()], V0)

            ##  167.70(1)(c)
            ##  c. After any surplus votes are calculated but not yet transferred, 
            ##     all candidates for whom it is mathematically impossible to be elected 
            ##     must be defeated simultaneously. 
            ##     Votes for the defeated candidates must be transferred to each ballot's 
            ##     next-ranked continuing candidate.

            #  fixSpec=True instructs the function to use the correct definition
            #  of mathematical certainty of defeat instead of the erroneous definition
            #  in 167.20.

            certainLosers = findCertainLosers(E.surplus, fixSpec=True)
            if certainLosers:
                for c in certainLosers:
                    c.defeat('Defeat certain loser')
                cids = [c.cid for c in certainLosers]
                for b in (b for b in E.ballots if b.topRank in cids):
                    transfer(b)
                for c in certainLosers:
                    c.vote = V0
                E.logAction('transfer', "Transfer defeated: %s" % ", ".join(str(c) for c in certainLosers))

                ##     If no candidate can be defeated mathematically, the tabulation must continue
                ##     as described in clause d. 
                ##     Otherwise, the tabulation must continue as described in clause a.
                
                #   By implication, the test for tabulation-complete given in 167.70(1)(f)
                #   must be performed here; otherwise too many candidates can be defeated.

                if len(C.hopeful()) <= E.seatsLeftToFill():
                    break
                continue  ## continue as described in clause a. # pragma: no cover (optimized out)

            ##  167.70(1)(d)
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

            #  elect candidate with largest surplus
            #  and transfer largest surplus
            #
            ## 167.20(Surplus fraction of a vote)
            ##     Surplus fraction of a vote = 
            ##     (Surplus of an elected candidate)/(Total votes cast for elected candidate), 
            ##     calculated to four (4) decimal places, ignoring any remainder. 
            ##
            if C.pending():
                high_vote = max(c.vote for c in C.pending())
                high_candidates = [c for c in C.pending() if c.vote == high_vote]
                high_candidate = breakTie(high_candidates, 'largest surplus')
                high_candidate.unpend('Elect and transfer surplus')
                surplus = high_candidate.vote - E.quota
                for b in (b for b in E.ballots if b.topRank == high_candidate.cid):
                    b.weight = (b.weight * surplus) / high_candidate.vote
                    transfer(b)
                high_candidate.vote = E.quota
                E.logAction('transfer', "Transfer surplus: %s (%s)" % (high_candidate.name, surplus))
                continue  ## continue as described in clause a.

            ##  167.70(1)(e)
            ##  e. If there are no transferable surplus votes, 
            ##     the candidate with the fewest votes is defeated. 
            ##     Votes for a defeated candidate are transferred at their transfer value 
            ##     to each ballot's next-ranked continuing candidate. 
            ##     Ties between candidates with the fewest votes must be decided by lot, 
            ##     and the candidate chosen by lot must be defeated. 
            ##     The result of the tie resolution must be recorded and reused 
            ##     in the event of a recount.

            #  find candidate(s) with lowest vote
            #  defeat candidate with lowest vote
            #
            if C.hopeful():
                low_vote = min(c.vote for c in C.hopeful())
                low_candidates = [c for c in C.hopeful() if c.vote == low_vote]
                low_candidate = breakTie(low_candidates, 'defeat low candidate')
                low_candidate.defeat('Defeat low candidate')
                for b in (b for b in E.ballots if b.topRank == low_candidate.cid):
                    transfer(b)
                low_candidate.vote = V0
                E.logAction('transfer', "Transfer defeated: %s" % low_candidate.name)

            ##  167.70(1)(f)
            ##  f. The procedures in clauses a. to e. must be repeated 
            ##     until the number of candidates whose vote total is equal to or greater than 
            ##     the threshold is equal to the number of seats to be filled, 
            ##     or until the number of continuing candidates is equal to the number of offices 
            ##     yet to be elected. 

            if len(C.hopeful()) <= E.seatsLeftToFill():
                break

            ##     In the case of a tie between two (2) continuing candidates, 
            ##     the tie must be decided by lot as provided in Minneapolis Charter Chapter 2, 
            ##     Section 12, and the candidate chosen by lot must be defeated. 
            ##     The result of the tie resolution must be recorded and reused in the event 
            ##     of a recount.

            # Note: this will happen, if necessary, at the next defeat-lowest step e above


        #  Tabulation complete.

        ##  167.70(1)(a)
        #   Elect continuing candidates with votes >= threshold
        for c in C.pending():
            c.unpend('Elect candidates with threshold votes')

        ##  167.70(1)(f)
        ##  f. ...
        ##     If the number of continuing candidates is equal to the number of offices 
        ##     yet to be elected, any remaining continuing candidates must be declared elected.
        #
        #  Note: implemented as "less than or equal to"
        #
        if 0 < len(C.hopeful()) <= E.seatsLeftToFill():
            for c in C.hopeful():
                c.elect('Elect remaining candidates')

        #  Defeat remaining hopeful candidates for reporting purposes
        #
        if len(C.hopeful()):
            for c in C.hopeful():
                c.defeat(msg='Defeat remaining candidates')
