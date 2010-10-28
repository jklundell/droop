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

from droop.common import UsageError
from electionrule import ElectionRule
from droop.election import CandidateSet

##  PRF Reference Rule: WIGM
##

class Rule(ElectionRule):
    '''
    Rule for counting PRF Reference WIGM elections

    Parameters: defeat_batch
    '''

    #  options
    #
    ##     D.4. Arithmetic. Truncate, with no rounding, the result of each
    ##          multiplication or division to four decimal places.
    defeatBatch = 'none'
    precision = 4   # fixed-arithmetic precision in digits
    name = 'wigm-prf'

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return cls.name

    @classmethod
    def tag(cls):
        "return a tag string for unit tests"
        return "%s-%s" % (cls.name, cls.defeatBatch)

    @classmethod
    def helps(cls, helps, name):
        "create help string for wigm"
        h =  "%s is the PR Foundation's Weighted Inclusive Gregory Method (WIGM) Reference STV.\n" % name
        h += '\noptions:\n'
        h += '  defeat_batch=(none*, losers): before surplus transfer, defeat sure losers\n'
        h += '    *default\n'
        helps[name] = h

    @classmethod
    def options(cls, options=dict(), used=set(), ignored=set()):
        "initialize election parameters"

        options['arithmetic'] = 'fixed'
        options['precision'] = cls.precision
        options['display'] = None
        ignored |= set(('arithmetic', 'precision', 'display'))

        cls.defeatBatch = options.get('defeat_batch', 'none')
        if cls.defeatBatch not in ('none', 'losers'):
            raise UsageError('unknown defeat_batch %s; use none or losers' % cls.defeatBatch)
        used |= set(('defeat_batch',))

        return options

    @classmethod
    def info(cls):
        "return an info string for the election report"
        if cls.defeatBatch == 'losers':
            return "PR Foundation WIGM Reference (batch defeat)"
        return "PR Foundation WIGM Reference (single defeat)"

    @classmethod
    def method(cls):
        "underlying method: meek, wigm or qpq"
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
            "Determine whether a candidate has a quota."
            return candidate.vote >= E.quota

        def calcQuota(E):
            "Calculate quota."
            ##  A. Initialize Election
            ##     Set the quota q (votes required for election) to the total
            ##     number of valid ballots divided by one more than the number of
            ##     seats to be filled, adding 0.0001 to the result. ...
            return V(E.nBallots) / V(E.nSeats+1) + V.epsilon

        def transfer(ballot, CS):
            "Transfer ballot to next hopeful candidate."
            while not ballot.exhausted and ballot.topCand not in CS.hopeful:
                ballot.advance()
            return not ballot.exhausted

        def breakTie(E, tied, reason=None, strong=True):
            '''
            break a tie

            purpose must be 'surplus' or 'elect' or 'defeat',
            indicating whether the tie is being broken for the purpose
            of choosing a surplus to transfer, a winner,
            or a candidate to defeat.

            Set strong to False to indicate that weak tiebreaking should be
            attempted, if relevant. Otherwise the tie is treated as strong.

            Not all tiebreaking methods will care about 'purpose' or 'strength',
            but the requirement is enforced for consistency of interface.
            '''
            ##     D.1. Break ties. Ties arise in B.4 (choose candidate for surplus
            ##          transfer) and in B.5 (choose candidate for defeat). In each
            ##          case, choose the tied candidate who is earliest in a
            ##          predetermined random tiebreaking order.
            ##
            if len(tied) == 1:
                return tied.pop()
            t = tied.byTieOrder()[0]
            names = ", ".join([c.name for c in tied])
            E.logAction('tie', 'Break tie (%s): [%s] -> %s' % (reason, names, t.name))
            return t

        def batchDefeat():
            "find the largest batch of sure losers"

            ##     B.3. Optional: Defeat sure losers. Find the largest set of
            ##          hopeful candidates that meets all of the following conditions.
            ##
            ##     B.3.a. The number of hopeful candidates not in the set is
            ##            greater than or equal to the number seats to be filled minus
            ##            pending and elected candidates).
            ##
            ##     B.3.b. For each candidate in the set, every hopeful candidate
            ##            with the same vote v or lower is also in the set.
            ##
            ##     B.3.c. The sum of the votes v of the candidates in the set plus
            ##            the sum of all the current surpluses s is less than the lowest
            ##            vote v of the hopeful candidates not in the set.
            ##
            ##        If the resulting set is not empty, defeat each candidate in
            ##        the set. Test count complete (D.3). Transfer each ballot
            ##        assigned to a defeated candidate (D.2). Continue at step B.1.
            ##

            #   calculate untransferred surplus
            #
            surplus = sum([(c.vote - E.quota) for c in CS.pending], V0)

            #   start with candidates sorted by vote
            #   build a sorted list of groups
            #     where each group consists of the candidates tied at that vote
            #     (when there's no tie, a group will have one candidate)
            #
            sortedCands = CS.hopeful.byVote()
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
            maxDefeat = len(CS.hopeful) - E.seatsLeftToFill()
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
            return CandidateSet(batch)

        #  Local variables for convenience
        #
        CS = E.CS   # candidate state
        V = E.V     # arithmetic value class
        V0 = E.V0   # constant zero

        ##  A. Initialize Election
        ##     Set the quota q (votes required for election) to the total
        ##     number of valid ballots divided by one more than the number of
        ##     seats to be filled, adding 0.0001 to the result. Set each
        ##     candidate who is not withdrawn to hopeful. Test count complete
        ##     (D.3). Set each ballot's weight w to one, and assign it to its
        ##     top-ranked hopeful candidate.

        #  calculate quota
        #
        E.quota = calcQuota(E)

        #  Calculate initial vote totals
        #
        for b in E.ballots:
            b.topCand.vote += b.vote

        ##     D.3. Test count complete. If the number of elected plus pending
        ##          candidates is equal to the number of seats to be filled, or the
        ##          number of elected plus pending plus hopeful candidates is equal
        ##          to or less than the number of seats to be filled, the count is
        ##          complete; finish at step C.
        ##
        while len(CS.hopeful) > E.seatsLeftToFill() > 0:

            ##  B. Round
            ##
            ##     B.1. Count votes. Initialize the vote v for each candidate to 0.
            ##          For each non-exhausted ballot, add the ballot's current weight w
            ##          to the vote v for the ballot's currently assigned candidate.
            ##
            E.newRound()

            ##     B.2. Elect winners. Set each hopeful candidate whose vote v is
            ##          greater than or equal to quota q to pending (elected with
            ##          surplus-transfer pending). Set the surplus s of each pending
            ##          candidate to v minus quota q. Test count complete (D.3).
            ##
            for c in [c for c in CS.hopeful.byVote(reverse=True) if hasQuota(E, c)]:
                CS.pend(c)      # elect with transfer pending

            ##     B.3. Optional: Defeat sure losers.
            ##          ...
            ##          If the resulting set is not empty, defeat each candidate in
            ##          the set. Test count complete (D.3). Transfer each ballot
            ##          assigned to a defeated candidate (D.2). Continue at step B.1.
            ##
            if cls.defeatBatch == 'losers':
                sureLosers = batchDefeat()
                if sureLosers:
                    for c in sureLosers.byBallotOrder():
                        CS.defeat(c, msg='Defeat sure loser')
                    if len(CS.hopeful) <= E.seatsLeftToFill():
                        break;
                    for c in sureLosers.byBallotOrder():
                        for b in (b for b in E.ballots if b.topRank == c.cid):
                            if transfer(b, CS):
                                b.topCand.vote += b.vote
                        c.vote = V0
                        E.logAction('transfer', "Transfer defeated: %s" % c)
                    continue

            ##     B.4. Transfer high surplus. Select the pending candidate c, if
            ##          any, with the largest surplus s (possibly zero), breaking ties
            ##          per procedure D.1. For each ballot assigned to c, set its new
            ##          weight w to the ballot's current weight w multiplied by c's
            ##          surplus s, then divided by c's total vote v. Transfer the ballot
            ##          (D.2). If a surplus (possibly zero) is transferred, continue at
            ##          step B.1.
            ##
            if CS.pending:
                high_vote = max(c.vote for c in CS.pending)
                high_candidates = CandidateSet([c for c in CS.pending if c.vote == high_vote])
                high_candidate = breakTie(E, high_candidates, 'surplus')
                CS.elect(high_candidate, 'Transfer high surplus')
                surplus = high_candidate.vote - E.quota

                for b in (b for b in E.ballots if b.topRank == high_candidate.cid):
                    b.weight = (b.weight * surplus) / high_candidate.vote
                    if transfer(b, CS):
                        b.topCand.vote += b.vote
                high_candidate.vote = E.quota
                E.logAction('transfer', "Surplus transferred: %s (%s)" % (high_candidate, V(surplus)))

            ##     B.5. Defeat low candidate. Defeat the hopeful candidate c with
            ##          the lowest vote v, breaking ties per procedure D.1. Test count
            ##          complete (D.3). Transfer each ballot assigned to the defeated
            ##          candidate (D.2). Continue at step B.1.
            ##
            elif CS.hopeful:
                #  find & defeat candidate with lowest vote
                #
                low_vote = min(c.vote for c in CS.hopeful)
                low_candidates = CandidateSet([c for c in CS.hopeful if c.vote == low_vote])
                low_candidate = breakTie(E, low_candidates, 'defeat')
                CS.defeat(low_candidate)
                for b in (b for b in E.ballots if b.topRank == low_candidate.cid):
                    if transfer(b, CS):
                        b.topCand.vote += b.vote
                low_candidate.vote = V0
                E.logAction('transfer', "Transfer defeated: %s" % low_candidate)

        ##  C. Finish Count
        ##     Set all pending candidates to elected. If all seats are
        ##     filled, defeat all hopeful candidates; otherwise elect all
        ##     hopeful candidates. Count is complete.
        #
        for c in CS.pending:
            CS.elect(c, msg='Elect pending')
        for c in list(CS.hopeful):
            if len(CS.elected) < E.nSeats:
                CS.elect(c, msg='Elect remaining')
            else:
                CS.defeat(c, msg='Defeat remaining')
