# -*- coding: utf-8 -*-
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
http://minneapolis-mn.elaws.us/code/coor_apxid29496_title8.5_ch167
as of 2018-07-12

The rule here reflects amendments c. 2013:
http://www.minneapolismn.gov/www/groups/public/@clerk/documents/webcontent/wcms1p-108666.pdf
More: http://vote.minneapolismn.gov/rcv/RCV-HISTORY

2017 sample results:
    single-winner (Mayor): http://vote.minneapolismn.gov/results/2017/2017-mayor-tabulation
    multiple-winner (Parks & Recreation Commissioner At Large)
        http://vote.minneapolismn.gov/results/2017/2017-park-board-at-large-tab

Minneapolis STV is a variation on WIGM,
using fixed-point decimal arithmetic with four digits of precision.

Implementation notes:

1. The current rule reflects amendments through 2013 as of 2018-07:
http://www.minneapolismn.gov/www/groups/public/@clerk/documents/webcontent/wcms1p-108666.pdf

2. 167.70(c)(1)d. is confusing. "The surplus of the candidate chosen by lot must be transferred
before other transfers are made": what are the "other transfers"? The general principle seems
(and ought) to be that each time a transfer is made, we go back to 167.70(c)(1)a. and then recalculate surpluses.

3. 167.70(c)(1)f. "If the number of continuing candidates is equal to the number of seats yet to be filled,
any remaining continuing candidates must be declared elected". Should be "less than or equal to", allowing
for the case of fewer candidates than seats to be filled (in which case, if the rules were strictly followed,
the count would never terminate).

4. The rule about not transferring votes from the last defeated candidate seems to be a holdover from
the single-winner rule 167.60(c)(1)b, so that we don't end up reporting a unanimous vote for the winner.
That doesn't really make sense for multiple-seat elections. Moreover, in the case of single-seat elections,
it would be helpful to report vote counts before and after such a final transfer, in order to quantify total
voter support for the ultimate winner, some of which is likely to be uncovered by the final transfer.
This goes to validating the assertion that RCV is "majority-seeking".

5. The tiebreaking rule requires the presence of the chief election official.
In their absence, this implementation uses an external tiebreaking order to break ties.
Ideally, the rule would be changed so that the official would predetermine a tiebreaking
order.

6. Droop doesn't identify undeclared write-in candidates. The best we can do, for now, is to mark
them as withdrawn. TODO: test to see what the reporting looks like.

7. "Surplus  means the total number of votes cast for an elected candidate in excess of the threshold."
Do we need to also included unelected candidates with a surplus? Relevant to finding certain losers? But
see 167.70(c)(1)b. "Surplus votes for any candidates whose vote total is equal to or greater than the threshold
must be calculated." (Note "any".)


Minneapolis Election Code

The relevant portions of the Minneapolis election code is reproduced below, and is also
distributed as comments marked with ## in the body of the implementation.


167.20. Definitions. The following words and phrases when used in this chapter shall have the
meanings respectively ascribed to them in this section:

Batch elimination  means a simultaneous defeat of multiple continuing candidates for whom it is
mathematically impossible to be elected.

Chief election official means the city clerk and includes the city clerk's designee(s).

Continuing candidate  means a candidate who has been neither elected nor defeated.

Declared write-in candidate(s)  means a candidate(s) who has filed a written request
in accordance with section 167.45.

Exhausted ballot  means a ballot that cannot be advanced under section 167.60(c)(2) or
section 167.70(c)(2).

Highest continuing ranking  means the ranking on a voter's ballot with the lowest numerical value
for a continuing candidate.

Mathematically impossible to be elected  means either:
   (1) The candidate could never win because his or her current vote total plus all votes that could
   possibly be transferred to him or her in future rounds (from candidates with fewer votes, tied
   candidates, surplus votes, and from undeclared write-in candidates) would not be enough to equal
   or surpass the candidate with the next higher current vote total; or

   (2) The candidate has a lower current vote total than a candidate who is described by (1).

Maximum possible threshold  means the number of votes sufficient for a candidate to be elected
under a first ranked choice tabulation under sections 167.60(b) and 167.70(b). In any given election,
the maximum possible threshold equals the total ballots cast that include votes, undervotes,
skipped rankings, or overvotes for the office, divided by the sum of one (1) plus the number of offices
to be filled, then adding one (1), disregarding any fractions. Maximum Possible Threshold =
((Total ballots cast that include votes, undervotes, skipped rankings, or overvotes for the office)
/(Seats to be elected + 1)) +1, with any fractions disregarded.

An overvote  occurs when a voter ranks more than one (1) candidate at the same ranking.

Partially defective ballot  means a ballot that is defective to the extent that the election judges
are unable to determine the voter's intent with respect to the office being counted.

Ranked-choice voting  means an election method in which voters rank candidates for an office in
order of their preference and the ballots are counted in rounds and votes, or fractions thereof,
are distributed to candidates according to the preferences marked on each ballot as described
in sections 167.60 and 167.70 of this chapter.

Ranked-choice voting tabulation center means one (1) or more locations selected by the chief election official
for the tabulation of votes.

Ranking  means the number assigned by a voter to a candidate to express the voter's preference for
that candidate. Ranking number one (1) is the highest ranking. A ranking of lower numerical value
indicates a greater preference for a candidate than a ranking of higher numerical value.

Repeat candidate ranking  occurs when a voter ranks the same candidate at multiple rankings
for the office being counted.

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
defective ballots, divided by the sum of one (1) plus the number of offices to be filled, then adding
one (1), disregarding any fractions. Threshold = ((Total votes cast)/(Seats to be
elected + 1)) +1, with any fractions disregarded.

Transfer value  means the fraction of a vote that a transferred ballot will contribute to the next
ranked continuing candidate on that ballot. The transfer value of a vote cast for an elected
candidate is calculated by multiplying the surplus fraction by its current value, calculated to four
(4) decimal places, ignoring any remainder. The transfer value of a vote cast for a defeated
candidate is the same as its current value.

Transferable vote  means a vote or a fraction of a vote for a candidate who has been either elected
or defeated.

Totally defective ballot  means a ballot that is defective to the extent that the election judges
are unable to determine the voter's intent for any office on the ballot.

Undeclared write-in candidate  means a write-in candidate who is not a declared write-in candidate.

An undervote  occurs when a voter does not rank any candidates for an office. (2008-Or-028, § 1,
4-18-08; 2009-Or-102, § 1, 10-2-09; 2013-Or-055, § 1, 5-24-13)


167.50. Tabulation of votes; in general
(c) Recording write-in votes. At a time set by the chief election official, the judges of the election
shall convene at a ranked-choice voting tabulation center to record the names and number of votes received
by each declared write-in candidate. The number of votes received by undeclared write-in candidates will be
recorded as a group by office. (2008-Or-028, § 1, 4-18-08; 2009-Or-102, § 3, 10-2-09; 2013-Or-055, § 5, 5-24-13)


167.70. - Tabulation of votes, multiple-seat elections.
(a) Applicability.
This section applies to a ranked-choice voting election in which more than
one (1) seat in office is to be filled from a single set of candidates on the ballot. The method
of tabulating ranked-choice votes for multiple-seat elections as described in this section must be
known as the "multiple-seat single transferable vote" method of tabulation.

(b) First ranked choice tabulation.
A first ranked choice tabulation shall be done under this clause before a tabulation as described in
clause (c). A first ranked choice tabulation will consist of a first round only. Under the first ranked
choice tabulation, the vote total will be the sum of the number one (1) ranked votes. The maximum possible
threshold must be determined. If the number of candidates, other than any undeclared or declared write-in
candidate, whose vote total is equal to or greater than the maximum possible threshold is equal to the
number of seats to be filled, those candidates are declared elected and the tabulation is complete.
If the number of candidates, other than any undeclared or declared write-in candidate, whose vote total
is equal to or greater than the maximum possible threshold is less than the number of seats to be filled,
a tabulation, as described in clause (c), shall be done.

(c) Tabulation of round(s).

(1) Tabulation of votes at the ranked-choice voting tabulation center must proceed in rounds for
each office to be counted. The threshold must be calculated. The sum of all ranked-choice votes
for every candidate must be calculated. Each round must proceed sequentially as follows:

    a. NEW ROUND
    The number of votes cast for each candidate for the current round must be counted.

    If the number of candidates, other than any undeclared write-in candidate, whose vote total is
    equal to or greater than the threshold is equal to the number of seats to be filled, those
    candidates who are continuing candidates are elected and the tabulation is complete.

    If the number of candidates, other than any undeclared write-in candidate, whose vote total is
    equal to or greater than the threshold is not equal to the number of seats to be filled, a new
    round begins and the tabulation must continue as described in clause b.

    b. CALCULATE SURPLUS
    Surplus votes for any candidates whose vote total is equal to or greater than the threshold
    must be calculated.

    c. DEFEAT CERTAIN LOSERS
    At the beginning of the second round only, after any surplus votes are calculated but not yet
    transferred, all undeclared write-in candidates and all candidates for whom it is mathematically
    impossible to be elected must be defeated simultaneously .

    For rounds subsequent to the second round, after any surplus votes are calculated but not yet
    transferred, all candidates for whom it is mathematically impossible to be elected must be
    defeated simultaneously.

    Votes for the defeated candidates must be transferred to each ballot's next-ranked continuing
    candidate, except votes for candidates defeated in the final round are not transferred if, by
    their defeat, the number of continuing candidates is reduced to the number of seats yet to be
    filled.

    If no candidate can be defeated under this clause, the tabulation must continue as described in
    clause d. Otherwise, the tabulation must continue as described in clause a.

    d. ELECT HIGHEST SURPLUS
    The candidate with the largest surplus is declared elected and that candidate's surplus is
    transferred.

    A tie between two (2) or more candidates must be resolved by lot by the chief election official.
    The surplus of the candidate chosen by lot must be transferred before other transfers are made.
    The result of the tie resolution must be recorded and reused in the event of a recount.

    The transfer value of each vote cast for an elected candidate must be transferred to the next
    continuing candidate on that ballot.

    If no candidate has a surplus, the tabulation must continue as described in clause e. Otherwise,
    the tabulation must continue as described in clause a.

    e. DEFEAT LOWEST CANDIDATE
    If there are no transferable surplus votes, the candidate with the fewest votes is defeated.

    Votes for a defeated candidate are transferred at their transfer value to each ballot's
    next-ranked continuing candidate, except votes for candidates defeated in the final round are
    not transferred if, by their defeat, the number of continuing candidates is reduced to the
    number of seats yet to be filled.

    Ties between candidates with the fewest votes must be resolved by lot by the chief election
    official, and the candidate chosen by lot must be defeated. The result of the tie resolution
    must be recorded and reused in the event of a recount.

    f. FINISH
    The procedures in clauses a. to e. must be repeated until the number of candidates whose vote
    total is equal to or greater than the threshold is equal to the number of seats to be filled, or
    until the number of continuing candidates is equal to the number of seats yet to be filled.

    If the number of continuing candidates is equal to the number of seats yet to be filled, any
    remaining continuing candidates must be declared elected. In the case of a tie between two (2)
    or more continuing candidates, the tie must be resolved by lot by the chief election official.
    The result of the tie resolution must be recorded and reused in the event of a recount.

    Candidates defeated under this clause in the final round will retain their votes.


(2) When a skipped ranking, overvote or repeat candidate ranking is encountered on a ballot, that
ballot shall count towards the highest continuing ranking that is not a skipped ranking, an overvote
or repeat candidate ranking. If any ballot cannot be advanced because no further continuing candidates
are ranked on that ballot, or because the only votes for further continuing candidates that are ranked
on that ballot are either overvotes or repeat candidate rankings, the ballot shall not count towards  any
candidate in that round or in subsequent rounds for the office being counted. (2008-Or-028, § 1, 4-18-08;
2009-Or-102, § 5, 10-2-09; 2013-Or-055, § 7, 5-24-13; 2015-Or-065 , § 4, 7-24-15)

167.75. - Ties resolved by lot.
(a) Who resolves a tie by lot. The chief election official must resolve a tie by lot.

(b) Notice to candidates with tied votes. The chief election official must notify all candidates
with tied votes that the tie will be resolved by lot, except those candidates who have not provided
contact information that would allow notice under this section. This notice must be sent at least
one (1) hour prior to resolving the tie by lot. The notice must be sent through a medium that would
generally be capable of reaching a person within the one-hour period, such as face-to-face, a fax,
an e-mail, an instant message, a text, a video chat, a telephone call, or a voicemail. The chief
election official may consider the preference of each candidate for the medium through which the
notice would be provided. The chief election official is not required to confirm that the notice
is received by a candidate before resolving a tie by lot. A tie may be resolved by lot even though
some or all of the candidates who have tied votes are not present.

(c) Witnesses. The resolving of the tie by lot must be witnessed by two (2) election judges who are
members of different major political parties.

(d) Video. The resolving of the tie by lot may be recorded through any audio and visual recording technology.

(e) Media. The chief election official may contact the media to view the chief election official resolve a tie by lot.

(f) Procedures. The chief election official may establish written procedures for implementing this section.
(2015-Or-065 , § 5, 7-24-15)
'''

from __future__ import absolute_import
from .electionmethods import MethodWIGM

class Rule(MethodWIGM):
    '''
    Rule for counting Minneapolis MN STV
    '''
    method = 'wigm' # underlying method
    name = 'mpls'
    quota_name = 'Threshold'

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return cls.name

    @classmethod
    def helps(cls, helps, name):
        "create help string for mpls"
        h = 'Minneapolis STV is a variant on WIGM.\n'
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
        "count the election with Minneapolis RCV-PR rules"

        #  local support functions
        #
        def hasQuota(candidate):
            '''
            Determine whether a candidate has a quota. [167.70(c)(1)a,d]
            '''
            return candidate.vote >= E.quota

        def calcQuota():
            '''
            Calculate quota. [167.20(Threshold)]
            '''
            ##  167.20(Threshold)
            ##  Threshold = ((Total votes cast)/(Seats to be elected + 1)) +1,
            ##  with any fractions disregarded.

            return V(E.nBallots // (E.nSeats + 1) + 1)

        def transfer(ballot):
            '''
            Transfer ballot to next continuing (hopeful or pending) candidate
            '''
            ##  167.70(c)(1)d.
            ##  The transfer value of each vote cast for an elected candidate must be transferred
            ##  to the next continuing candidate on that ballot. ...
            ##
            ##  167.70(c)(1)e.
            ##  ... Votes for a defeated candidate are transferred at their transfer value to each
            ##  ballot's next-ranked continuing candidate.

            while not ballot.exhausted and ballot.topCand not in C.hopeful() + C.pending():
                ballot.advance()
            if ballot.exhausted:
                E.exhausted += ballot.vote
            else:
                ballot.topCand.vote += ballot.vote

        def findCertainLosers(surplus):
            '''
            Find the group of candidates that cannot be elected per 167.20
            '''
            ## 167.20. Mathematically impossible to be elected means either:
            ##         (1) The candidate could never win because his or her current vote total
            ##             plus all votes that could possibly be transferred to him or her
            ##             in future rounds (from candidates with fewer votes, tied candidates,
            ##             surplus votes, and from undeclared write-in candidates)
            ##             would not be enough to equal or surpass the candidate
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
                #   skip if vote added to surplus equals or surpasses the vote for
                #   a candidate in the next-higher group
                #
                if (vote + surplus) >= sortedGroups[g+1][0].vote:
                    continue
                losers = list(maybe)
            return C.byBallotOrder(losers)

        def breakTie(tied, reason=None):
            '''
            break a tie by lot [167.70(c)(1)f.]
            '''
            ##      Ties between candidates with the fewest votes must be resolved by lot by the chief election
            ##      official, and the candidate chosen by lot must be defeated. The result of the tie resolution
            ##      must be recorded and reused in the event of a recount.

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
        ##  167.70(c)(1)a.
        ##  The number of votes cast for each candidate for the current round must be counted.
        ##
        for b in E.ballots:
            b.topCand.vote += b.vote
        E.exhausted = V0    # track non-transferable votes

        E.newRound()    # Round 1
        while True:

            ##  167.70(c)(1)a. NEW ROUND
            ##  If the number of candidates, other than any undeclared write-in candidate, whose vote total is
            ##  equal to or greater than the threshold is equal to the number of seats to be filled, those
            ##  candidates who are continuing candidates are elected and the tabulation is complete.

            ##  167.70(c)(1)b. CALCULATE SURPLUS
            ##  Surplus votes for any candidates whose vote total is equal to or greater than the threshold
            ##  must be calculated.
            #
            #   Note that we calculate the surplus early, for reporting purposes. This does not result
            #   in any change in outcome.

            E.surplus = sum([c.surplus for c in C], V0)

            E.logAction('count', 'Count Votes')
            hopefulWithQuota = [c for c in C.hopeful(order='vote', reverse=True) if hasQuota(c)]
            if (len(C.elected()) + len(hopefulWithQuota)) >= E.nSeats:
                for c in hopefulWithQuota:
                    c.elect('Candidate at threshold', pending=False)
                break

            ##  167.70(c)(1)a.
            ##  If the number of candidates, other than any undeclared write-in candidate, whose vote total is
            ##  equal to or greater than the threshold is not equal to the number of seats to be filled, a new
            ##  round begins and the tabulation must continue as described in clause b.

            E.newRound()

            ##  167.70(c)(1)c. DEFEAT CERTAIN LOSERS
            ##  At the beginning of the second round only, after any surplus votes are calculated but not yet
            ##  transferred, all undeclared write-in candidates and all candidates for whom it is mathematically
            ##  impossible to be elected must be defeated simultaneously .
            ##
            ##  For rounds subsequent to the second round, after any surplus votes are calculated but not yet
            ##  transferred, all candidates for whom it is mathematically impossible to be elected must be
            ##  defeated simultaneously.
            ##
            ##  Votes for the defeated candidates must be transferred to each ballot's next-ranked continuing
            ##  candidate, except votes for candidates defeated in the final round are not transferred if, by
            ##  their defeat, the number of continuing candidates is reduced to the number of seats yet to be
            ##  filled.

            def defeatGroup(group, groupName):
                '''
                Defeat and transfer a (possibly empty) group of candidates,
                returning True if at least one candidate was defeated.
                '''
                if group:
                    for c in group:
                        c.defeat('Defeat %s' % groupName)
                    for b in (b for b in E.ballots if b.topRank in [c.cid for c in group]):
                        transfer(b)
                    for c in group:
                        c.vote = V0
                    E.surplus = sum([c.surplus for c in C], V0)
                    E.logAction('transfer', "Transfer defeated: %s" % ", ".join(str(c) for c in group))
                    return True
                return False

            if E.round >= 2:
                defeated = False
                if E.round == 2:
                    defeated = defeatGroup([c for c in C.hopeful() if c.isUndeclared], "undeclared write-in")
                print >> sys.stderr, "** mpls defeat certain losers: surplus=%s" % E.surplus
                defeated = defeated or defeatGroup(findCertainLosers(E.surplus), "certain loser")

                    ##  167.70(c)(1)c.
                    ##  If no candidate can be defeated under this clause, the tabulation must continue as described in
                    ##  clause d. Otherwise, the tabulation must continue as described in clause a.

                if defeated:
                    continue    # pragma: no cover (optimized out)

            ##  167.70(c)(1)d. ELECT HIGHEST SURPLUS
            ##  The candidate with the largest surplus is declared elected and that candidate's surplus is
            ##  transferred.
            ##
            ##  A tie between two (2) or more candidates must be resolved by lot by the chief election official.
            ##  The surplus of the candidate chosen by lot must be transferred before other transfers are made.
            ##  The result of the tie resolution must be recorded and reused in the event of a recount.
            ##
            ##  The transfer value of each vote cast for an elected candidate must be transferred to the next
            ##  continuing candidate on that ballot.
            ##
            ##  If no candidate has a surplus, the tabulation must continue as described in clause e. Otherwise,
            ##  the tabulation must continue as described in clause a.

            hopefulWithQuota = [c for c in C.hopeful(order='vote', reverse=True) if hasQuota(c)]
            if hopefulWithQuota:
                high_vote = max(c.vote for c in hopefulWithQuota)
                high_candidates = [c for c in hopefulWithQuota if c.vote == high_vote]
                high_candidate = breakTie(high_candidates, 'largest surplus')
                high_candidate.elect('Elect', pending=False)
                ##
                ## 167.20(Surplus fraction of a vote)
                ##     Surplus fraction of a vote =
                ##     (Surplus of an elected candidate)/(Total votes cast for elected candidate),
                ##     calculated to four (4) decimal places, ignoring any remainder.
                ##
                surplus = high_candidate.vote - E.quota
                for b in (b for b in E.ballots if b.topRank == high_candidate.cid):
                    b.weight = (b.weight * surplus) / high_candidate.vote
                    transfer(b)
                high_candidate.vote = E.quota
                E.surplus = sum([c.surplus for c in C], V0)
                E.logAction('transfer', "Transfer surplus: %s (%s)" % (high_candidate.name, surplus))
                continue  ## continue as described in clause a.

            ##  167.70(c)(1)e. DEFEAT LOWEST CANDIDATE
            ##  If there are no transferable surplus votes, the candidate with the fewest votes is defeated.
            ##
            ##  Votes for a defeated candidate are transferred at their transfer value to each ballot's
            ##  next-ranked continuing candidate, except votes for candidates defeated in the final round are
            ##  not transferred if, by their defeat, the number of continuing candidates is reduced to the
            ##  number of seats yet to be filled.
            ##
            ##  Ties between candidates with the fewest votes must be resolved by lot by the chief election
            ##  official, and the candidate chosen by lot must be defeated. The result of the tie resolution
            ##  must be recorded and reused in the event of a recount.

            if len(C.hopeful()) > E.seatsLeftToFill():
                #
                #  find & defeat candidate with lowest vote, breaking ties
                #
                low_vote = min(c.vote for c in C.hopeful())
                low_candidates = [c for c in C.hopeful() if c.vote == low_vote]
                low_candidate = breakTie(low_candidates, 'defeat low candidate')
                low_candidate.defeat('Defeat low candidate')
                if len(C.hopeful()) > E.seatsLeftToFill(): # if not last round
                    for b in (b for b in E.ballots if b.topRank == low_candidate.cid):
                        transfer(b)
                    low_candidate.vote = V0
                    E.surplus = sum([c.surplus for c in C], V0)
                    E.logAction('transfer', "Transfer defeated: %s" % low_candidate.name)

            ##  167.70(c)(1)f. FINISH
            ##  The procedures in clauses a. to e. must be repeated until the number of candidates whose vote
            ##  total is equal to or greater than the threshold is equal to the number of seats to be filled, or
            ##  until the number of continuing candidates is equal to the number of seats yet to be filled.

            if len(C.hopeful()) <= E.seatsLeftToFill():
                break

        #  Tabulation complete.

        ##  167.70(c)(1)f. FINISH
        ##     ...
        ##  If the number of continuing candidates is equal to the number of seats yet to be filled, any
        ##  remaining continuing candidates must be declared elected. In the case of a tie between two (2)
        ##  or more continuing candidates, the tie must be resolved by lot by the chief election official.
        ##  The result of the tie resolution must be recorded and reused in the event of a recount.
        ##
        ##  Candidates defeated under this clause in the final round will retain their votes.

        if len(C.hopeful()) <= E.seatsLeftToFill():
            for c in C.hopeful():
                c.elect('Elect remaining candidates')

        #  Defeat remaining hopeful candidates for reporting purposes
        #
        if C.hopeful():
            for c in C.hopeful():
                c.defeat(msg='Defeat remaining candidates')
