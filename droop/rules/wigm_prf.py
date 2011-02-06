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


PRF Reference Rule: WIGM

A. Initialize Election
   A.1. Set the quota (votes required for election) to the total number of
        valid ballots, divided by one more than the number of seats to be
        filled, plus 0.0001.
   A.2. Set each candidate who is not withdrawn to hopeful.
   A.3. Test count complete (D.3).
   A.4. Set each ballot's weight to one, and assign it to its top-ranked
        hopeful candidate.
   A.5. Set the vote for each candidate to the total number of ballots
        assigned to that candidate.

B. Round
   B.1. Elect winners. Set each hopeful candidate whose vote is greater than
        or equal to the quota to pending (elected with surplus-transfer
        pending). Set the surplus of each pending candidate to that candidate's
        vote minus the quota. Test count complete (D.3).
   B.2. Defeat sure losers (optional). Find the largest set of hopeful
        candidates that meets all of the following conditions.
        B.2.a. The number of hopeful candidates not in the set is greater
               than or equal to the number seats to be filled minus pending and
               elected candidates).
        B.2.b. For each candidate in the set, each hopeful candidate with the
               same vote or lower is also in the set.
        B.2.c. The sum of the votes of the candidates in the set plus the sum
               of all the current surpluses (B.1) is less than the lowest vote
               of the hopeful candidates not in the set.
        If the resulting set is not empty, defeat each candidate in the set
        and test count complete (D.3), transfer each ballot assigned to a
        defeated candidate (D.2), and continue at step B.1.
   B.3. Transfer high surplus. Select the pending candidate, if any, with
        the largest surplus (possibly zero), breaking ties per procedure D.1.
        For each ballot assigned to that candidate, set its new weight to the
        ballot's current weight multiplied by the candidate's surplus (B.1),
        then divided by the candidate's total vote. Transfer the ballot (D.2).
        If a surplus (possibly zero) is transferred, continue at step B.1.
   B.4. Defeat low candidate. Defeat the hopeful candidate with the lowest
        vote, breaking ties per procedure D.1. Test count complete (D.3).
        Transfer each ballot assigned to the defeated candidate (D.2). Continue
        at step B.1.

C. Finish Count
   Set all pending candidates to elected. If all seats are filled, defeat all
   hopeful candidates; otherwise elect all hopeful candidates. Count is complete.

D. General Procedures
   D.1. Break ties. Ties arise in B.3 (choose candidate for surplus
        transfer) and in B.4 (choose candidate for defeat). In each case,
        choose the tied candidate who is earliest in a predetermined random
        tiebreaking order.
   D.2. Transfer ballots. Reassign each ballot to be transferred to its
        highest-ranking hopeful candidate and add the current weight of the
        ballot to the vote of that candidate. If the ballot ranks no such
        candidate, or has a weight of zero, it is exhausted and no longer
        participates in the count.
   D.3. Test count complete. If the number of elected plus pending
        candidates is equal to the number of seats to be filled, or the number
        of elected plus pending plus hopeful candidates is equal to or less
        than the number of seats to be filled, the count is complete; finish at
        step C.
   D.4. Arithmetic. Truncate, with no rounding, the result of each
        multiplication or division to four decimal places.
'''

from __future__ import absolute_import
from .electionmethods import MethodWIGM

class Rule(MethodWIGM):
    '''
    Rule for counting PRF Reference WIGM elections

    Parameters: batch defeat of sure losers selected by rule name
    '''

    #  options
    #
    ##     D.4. Arithmetic. Truncate, with no rounding, the result of each
    ##          multiplication or division to four decimal places.
    ##
    method = 'wigm'     # underlying method
    precision = 4       # fixed-arithmetic precision in digits

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return ('wigm-prf', 'wigm-prf-batch')

    @classmethod
    def helps(cls, helps, name):
        "create help string for wigm-prf"
        h =  "%s is the PR Foundation's Weighted Inclusive Gregory Method (WIGM) Reference STV.\n" % name
        if name.endswith('batch'):
            h += '  (defeat sure losers)\n'
        else:
            h += '  (single defeat)\n'
        h += '\noptions: none\n'
        helps[name] = h

    def __init__(self, E):
        "initialize rule"
        self.E = E
        self.defeat_batch = None
        self.name = None

    def options(self):
        "initialize election parameters"

        self.name = self.E.options.getopt('rule')
        self.defeat_batch = self.name.endswith('batch')
        self.E.options.setopt('arithmetic', default='fixed', force=True)
        self.E.options.setopt('precision', default=self.precision, force=True)
        self.E.options.setopt('display', default=self.precision, force=True)

    def info(self):
        "return an info string for the election report"
        if self.defeat_batch:
            return "PR Foundation WIGM Reference (defeat sure losers)"
        return "PR Foundation WIGM Reference (single defeat)"

    def tag(self):
        "return a tag string for unit tests"
        return self.name

    #########################
    #
    #   Main Election Counter
    #
    #########################
    def count(self):
        "count the election"

        #  local support functions
        #
        def hasQuota(candidate):
            "Determine whether a candidate has a quota."
            return candidate.vote >= E.quota

        def calcQuota():
            "Calculate quota."
            ##     A.1. Set the quota (votes required for election) to the total number of
            ##          valid ballots, divided by one more than the number of seats to be
            ##          filled, plus 0.0001.
            ##
            return V(E.nBallots) / V(E.nSeats+1) + V.epsilon

        def transfer(ballot):
            "Transfer ballot to next hopeful candidate."
            while not ballot.exhausted and ballot.topCand not in C.hopeful():
                ballot.advance()
            if ballot.exhausted:
                E.exhausted += ballot.vote
            else:
                ballot.topCand.vote += ballot.vote

        def breakTie(E, tied, reason=None):
            '''
            break a tie

            reason must be 'surplus' or 'elect' or 'defeat',
            indicating whether the tie is being broken for the purpose
            of choosing a surplus to transfer, a winner,
            or a candidate to defeat.
            '''
            ##     D.1. Break ties. Ties arise in B.3 (choose candidate for surplus
            ##          transfer) and in B.4 (choose candidate for defeat). In each case,
            ##          choose the tied candidate who is earliest in a predetermined random
            ##          tiebreaking order.
            ##
            if len(tied) == 1:
                return tied.pop()
            t = C.byTieOrder(tied)[0]
            names = ", ".join([c.name for c in tied])
            E.logAction('tie', 'Break tie (%s): [%s] -> %s' % (reason, names, t.name))
            return t

        def batchDefeat():
            "find the largest batch of sure losers"

            ##     B.2. Defeat sure losers (optional). Find the largest set of hopeful
            ##          candidates that meets all of the following conditions.
            ##          B.2.a. The number of hopeful candidates not in the set is greater
            ##                 than or equal to the number seats to be filled minus pending and
            ##                 elected candidates).
            ##          B.2.b. For each candidate in the set, each hopeful candidate with the
            ##                 same vote or lower is also in the set.
            ##          B.2.c. The sum of the votes of the candidates in the set plus the sum
            ##                 of all the current surpluses (B.1) is less than the lowest vote
            ##                 of the hopeful candidates not in the set.
            ##          If the resulting set is not empty, defeat each candidate in the set
            ##          and test count complete (D.3), transfer each ballot assigned to a
            ##          defeated candidate (D.2), and continue at step B.1.
            ##

            #   calculate untransferred surplus
            #
            surplus = sum([(c.vote - E.quota) for c in C.pending()], V0)

            #   start with candidates sorted by vote
            #   build a sorted list of groups
            #     where each group consists of the candidates tied at that vote
            #     (when there's no tie, a group will have one candidate)
            #
            sortedCands = C.hopeful(order='vote')
            sortedGroups = []
            group = []
            vote = V0
            for c in sortedCands:
                if (vote + surplus) >= c.vote:
                    group.append(c)  # add candidate to tied group
                else:
                    if group:
                        sortedGroups.append(group)
                    group = [c]      # start a new group
                    vote = c.vote
            if group:
                sortedGroups.append(group)

            #   Scan the groups to find the biggest set of lowest-vote
            #   'sure-loser' candidates such that:
            #     * we leave enough hopeful candidates to fill the remaining seats (B.3.a)
            #     * we don't break up tied groups of candidates (B.3.b)
            #     * the total of the surplus and the votes for the defeated batch
            #       is less than the next-higher candidate (B.3.c)
            #
            #   We never defeat the last group, because that would mean
            #   defeating all the hopeful candidates, and if that's possible,
            #   the election is already complete and we wouldn't be here.
            #
            vote = V0
            maxDefeat = len(C.hopeful()) - E.seatsLeftToFill()
            maxg = None
            ncand = 0
            for g in xrange(len(sortedGroups) - 1):
                group = sortedGroups[g]
                ncand += len(group)
                if ncand > maxDefeat:
                    break  # too many defeats
                vote += sum([c.vote for c in group], V0)
                if (vote + surplus) < sortedGroups[g+1][0].vote:
                    maxg = g  # sure losers
            batch = []
            if maxg is not None:
                for g in xrange(maxg+1):
                    batch.extend(sortedGroups[g])
            return batch

        #  Local variables for convenience
        #
        E = self.E  # election object
        C = E.C     # candidates
        V = E.V     # arithmetic value class
        V0 = E.V0   # constant zero

        ##  A. Initialize Election
        ##     A.1. Set the quota (votes required for election) to the total number of
        ##          valid ballots, divided by one more than the number of seats to be
        ##          filled, plus 0.0001.
        ##     A.2. Set each candidate who is not withdrawn to hopeful.
        ##     A.3. Test count complete (D.3).
        ##     A.4. Set each ballot's weight to one, and assign it to its top-ranked
        ##          hopeful candidate.
        ##     A.5. Set the vote for each candidate to the total number of ballots
        ##          assigned to that candidate.
        ##
        E.quota = calcQuota()
        for b in E.ballots:
            b.topCand.vote += b.vote
        E.exhausted = V0  # track non-transferable votes

        ##     D.3. Test count complete. If the number of elected plus pending
        ##          candidates is equal to the number of seats to be filled, or the number
        ##          of elected plus pending plus hopeful candidates is equal to or less
        ##          than the number of seats to be filled, the count is complete; finish at
        ##          step C.
        ##
        E.logAction('begin', 'Begin Count')
        while len(C.hopeful()) > E.seatsLeftToFill() > 0:

            ##  B. Round
            ##
            E.newRound()

            ##     B.1. Elect winners. Set each hopeful candidate whose vote is greater than
            ##          or equal to the quota to pending (elected with surplus-transfer
            ##          pending). Set the surplus of each pending candidate to that candidate's
            ##          vote minus the quota. Test count complete (D.3).
            ##
            for c in [c for c in C.hopeful(order='vote', reverse=True) if hasQuota(c)]:
                c.elect(pending=True)      # elect with transfer pending

            ##     B.2. Defeat sure losers (optional). Find the largest set of hopeful
            ##          candidates that meets all of the following conditions.
            ##          ...
            ##          If the resulting set is not empty, defeat each candidate in the set
            ##          and test count complete (D.3), transfer each ballot assigned to a
            ##          defeated candidate (D.2), and continue at step B.1.
            ##
            if self.defeat_batch:
                sureLosers = batchDefeat()
                if sureLosers:
                    for c in C.byBallotOrder(sureLosers):
                        c.defeat(msg='Defeat sure loser')
                    if len(C.hopeful()) <= E.seatsLeftToFill():
                        break
                    cids = [c.cid for c in sureLosers]
                    for b in (b for b in E.ballots if b.topRank in cids):
                        transfer(b)
                    for c in sureLosers:
                        c.vote = V0
                    E.logAction('transfer', "Transfer defeated: %s" % ", ".join(str(c) for c in sureLosers))
                    continue

            ##     B.3. Transfer high surplus. Select the pending candidate, if any, with
            ##          the largest surplus (possibly zero), breaking ties per procedure D.1.
            ##          For each ballot assigned to that candidate, set its new weight to the
            ##          ballot's current weight multiplied by the candidate's surplus (B.1),
            ##          then divided by the candidate's total vote. Transfer the ballot (D.2).
            ##          If a surplus (possibly zero) is transferred, continue at step B.1.
            ##
            if C.pending():
                high_vote = max(c.vote for c in C.pending())
                high_candidates = [c for c in C.pending() if c.vote == high_vote]
                high_candidate = breakTie(E, high_candidates, 'surplus')
                high_candidate.unpend('Transfer high surplus')
                surplus = high_candidate.vote - E.quota

                for b in (b for b in E.ballots if b.topRank == high_candidate.cid):
                    b.weight = (b.weight * surplus) / high_candidate.vote
                    transfer(b)
                high_candidate.vote = E.quota
                E.logAction('transfer', "Surplus transferred: %s (%s)" % (high_candidate, surplus))

            ##     B.4. Defeat low candidate. Defeat the hopeful candidate with the lowest
            ##          vote, breaking ties per procedure D.1. Test count complete (D.3).
            ##          Transfer each ballot assigned to the defeated candidate (D.2). Continue
            ##          at step B.1.
            ##
            elif C.hopeful():
                #  find & defeat candidate with lowest vote
                #
                low_vote = min(c.vote for c in C.hopeful())
                low_candidates = [c for c in C.hopeful() if c.vote == low_vote]
                low_candidate = breakTie(E, low_candidates, 'defeat')
                low_candidate.defeat()
                for b in (b for b in E.ballots if b.topRank == low_candidate.cid):
                    transfer(b)
                low_candidate.vote = V0
                E.logAction('transfer', "Transfer defeated: %s" % low_candidate)

        ##  C. Finish Count
        ##     Set all pending candidates to elected. If all seats are filled, defeat all
        ##     hopeful candidates; otherwise elect all hopeful candidates. Count is complete.
        ##
        ##
        for c in C.pending():
            c.unpend()
        for c in C.hopeful():
            if len(C.elected()) < E.nSeats:
                c.elect(msg='Elect remaining')
            else:
                c.defeat(msg='Defeat remaining')
