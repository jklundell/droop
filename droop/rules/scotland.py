'''
Count election using Scottish STV rules

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

The Scottish Local Government Elections Order 2007
http://www.opsi.gov.uk/legislation/scotland/ssi2007/pdf/ssi_20070042_en.pdf
as of 2007-02-09

Scottish STV is a variation on WIGM,
using fixed-point decimal arithmetic with five digits of precision.

45. First stage
    (1) The returning officer shall sort the valid ballot papers into parcels according to the 
        candidates for whom first preference votes are given.
    (2) The returning officer shall then-
        (a) count the number of ballot papers in each parcel;
        (b) credit the candidate receiving the first preference vote with one vote for each ballot paper; and
        (c) record those numbers. 
    (3) The returning officer shall also ascertain and record the total number of valid ballot papers.

46. The quota
    (1) The returning officer shall divide the total number of valid ballot papers for the 
        electoral ward by a number exceeding by one the number of councillors to be elected 
        at the election for that electoral ward.
    (2) The result of the division under paragraph (1) (ignoring any decimal places), increased by one, 
        is the number of votes needed to secure the return of a candidate as a councillor 
        (in these rules referred to as the "quota").

47. Return of councillors
    (1) Where, at any stage of the count, the number of votes for a candidate equals or exceeds the quota, 
        the candidate is deemed to be elected.
    (2) A candidate is returned as a councillor when declared to be elected in accordance with rule 55(a).

48. Transfer of ballot papers
    (1) Where, at the end of any stage of the count, the number of votes credited to any candidate 
        exceeds the quota and, subject to rules 49 and 52, one or more vacancies remain to be filled, 
        the returning officer shall sort the ballot papers received by that candidate into further parcels 
        so that they are grouped-
        (a) according to the next available preference given on those papers; and
        (b) where no such preference is given, as a parcel of non-transferable papers.
    (2) The returning officer shall, in accordance with this rule and rule 49, transfer each parcel 
        of ballot papers referred to in paragraph (1)(a) to the continuing candidate for whom the next 
        available preference is given on those papers and shall credit such continuing candidates with 
        an additional number of votes calculated in accordance with paragraph (3).
    (3) The vote on each ballot paper transferred under paragraph (2) shall have a value ("the transfer value") 
        calculated as follows-
        Where
            A divided by B
            A = the value which is calculated by multiplying the surplus of the transferring candidate 
                by the value of the ballot paper when received by that candidate; and
            B = the total number of votes credited to that candidate, the calculation being made 
                to five decimal places (any remainder being ignored).
    (4) For the purposes of paragraph (3)-
        (a) "transferring candidate" means the candidate from whom the ballot paper is being transferred; and
        (b) "the value of the ballot paper" means-
            (i) for a ballot paper on which a first preference vote is given for the transferring candidate, one; and
            (ii) in all other cases, the transfer value of the ballot paper when received by the transferring candidate.

49. Transfer of ballot papers - supplementary provisions
    (1) If, at the end of any stage of the count, the number of votes credited to two or more candidates 
        exceeds the quota the returning officer shall-
        (a) first sort the ballot papers of the candidate with the highest surplus; and
        (b) then transfer the transferable papers of that candidate.
    (2) If the surpluses determined in respect of two or more candidates are equal, the transferable papers 
        of the candidate who had the highest number of votes at the end of the most recent preceding stage 
        at which they had unequal numbers of votes shall be transferred first.
    (3) If the numbers of votes credited to two or more candidates were equal at all stages of the count, 
        the returning officer shall decide, by lot, which candidate's transferable papers are to be transferred first.

50. Exclusion of candidates
    (1) If, one or more vacancies remain to be filled and-
        (a) the returning officer has transferred all ballot papers which are required by rule 48 
            or this rule to be transferred; or 
        (b) there are no ballot papers to be transferred under rule 48 or this rule,
            the returning officer shall exclude from the election at that stage the candidate with the then 
            lowest number of votes.
    (2) The returning officer shall sort the ballot papers for the candidate excluded under paragraph (1) 
        into parcels so that they are grouped-
        (a) according to the next available preference given on those papers; and
        (b) where no such preference is given, as a parcel of non-transferable papers.
    (3) The returning officer shall, in accordance with this article, transfer each parcel of ballot papers 
        referred to in paragraph (2)(a) to the continuing candidate for whom the next available preference 
        is given on those papers and shall credit such continuing candidates with an additional number of votes 
        calculated in accordance with paragraph (4).
    (4) The vote on each ballot paper transferred under paragraph (3) shall have a transfer value of one 
        unless the vote was transferred to the excluded candidate in which case it shall have the same 
        transfer value as when transferred to the candidate excluded under paragraph (1).
    (5) This rule is subject to rule 52.

51. Exclusion of candidates - supplementary provisions
    (1) If, when a candidate has to be excluded under rule 50- 
        (a) two or more candidates each have the same number of votes; and 
        (b) no other candidate has fewer votes,
        paragraph (2) applies. 
    (2) Where this paragraph applies-
        (a) regard shall be had to the total number of votes credited to those candidates 
            at the end of the most recently preceding stage of the count at which they had an unequal number 
            of votes and the candidate with the lowest number of votes at that stage shall be excluded; and
        (b) where the number of votes credited to those candidates was equal at all stages, 
            the returning officer shall decide, by lot, which of those candidates is to be excluded.

52. Filling of last vacancies
    (1) Where the number of continuing candidates is equal to the number of vacancies remaining unfilled, 
        the continuing candidates are deemed to be elected.
    (2) Where the last vacancies can be filled under this rule, no further transfer shall be made.
'''

from __future__ import absolute_import
from .electionmethods import MethodWIGM

class Rule(MethodWIGM):
    '''
    Rule for counting Scottish STV
    '''
    method = 'wigm' # underlying method
    name = 'scotland'

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return cls.name

    @classmethod
    def helps(cls, helps, name):
        "provide help string for Scottish STV"
        h =  'Scottish STV is a variant on WIGM.\n'
        h += '\nThere are no options.\n'
        h += '  arithmetic: fixed\n'
        h += '  precision=5\n'
        helps[name] = h
        
    def __init__(self, E):
        "initialize rule"
        self.E = E

    def options(self):
        "initialize election parameters"

        #  initialize and return arithmetic
        #
        #  arithmetic is fixed decimal, five digits of precision
        #  [48(3)]
        #
        #  (override arithmetic parameters)
        #
        self.E.options.setopt('arithmetic', default='fixed', force=True)
        self.E.options.setopt('precision', default=5, force=True)
        self.E.options.setopt('display', default=5, force=True)

    def info(self):
        "return an info string for the election report"
        return "Scottish STV"
        
    def tag(self):
        "return a tag string for unit tests"
        return self.name

    #########################
    #
    #   Main Election Counter
    #
    #########################
    def count(self):
        "count the election with Scottish STV rules"

        #  local support functions
        #
        def hasQuota(candidate):
            '''
            Determine whether a candidate has a quota. [47]
            '''
            return candidate.vote >= E.quota

        def calcQuota():
            '''
            Calculate quota. [46]
            '''
            ## 46. The quota
            ##     (1) The returning officer shall divide the total number of valid ballot papers for the 
            ##         electoral ward by a number exceeding by one the number of councillors to be elected 
            ##         at the election for that electoral ward.
            ##     (2) The result of the division under paragraph (1) (ignoring any decimal places), increased by one, 
            ##         is the number of votes needed to secure the return of a candidate as a councillor 
            ##         (in these rules referred to as the "quota").
            
            return V(E.nBallots // (E.nSeats + 1) + 1)

        def transfer(ballot):
            '''
            Transfer ballot to next continuing (hopeful) candidate. [48,49]
            '''
            while not ballot.exhausted and ballot.topCand not in C.hopeful():
                ballot.advance()
            if ballot.exhausted:
                E.exhausted += ballot.vote
            else:
                ballot.topCand.vote += ballot.vote

        def breakTie(tied, reason=None):
            '''
            break a tie by most-recent difference or by lot [49,51]
            '''
            if len(tied) == 1:
                return tied.pop()
            names = ", ".join([c.name for c in tied])
            direction = 0 if reason.find('defeat') >= 0 else -1
            tiedlist = list(tied)
            for n in xrange(E.round-1, -1, -1):
                tiedCids = [c.cid for c in tiedlist]
                CSR = E.rounds[n] # candidate states in round n
                tiedlist = C.byVote([c for c in CSR if c.cid in tiedCids])
                tiedlist = [c for c in tiedlist if c.vote == tiedlist[direction].vote]
                if len(tiedlist) == 1:
                    t = tiedlist[0]
                    E.logAction('tie', 'Break tie by prior stage (%s): [%s] -> %s' % (reason, names, t.name))
                    for c in tied:
                        if c.cid == t.cid:
                            return c
            t = C.byTieOrder(tiedlist)[0]
            E.logAction('tie', 'Break tie by lot (%s): [%s] -> %s' % (reason, names, t.name))
            for c in tied:
                if c.cid == t.cid:
                    return c

        def countComplete():
            '''
            test for count complete
            '''
            if E.seatsLeftToFill() <= 0:
                return True
            if len(C.hopeful()) <= E.seatsLeftToFill():
                return True
            return False

        #########################
        #
        #   COUNT THE ELECTION
        #
        #########################

        E = self.E  # election object
        C = E.C     # candidates
        V = E.V     # arithmetic value class
        V0 = E.V0   # constant zero

        #  Calculate quota per [46]
        #
        E.quota = calcQuota()

        #  count first-preference votes [45]
        #
        for b in E.ballots:
            b.topCand.vote += b.vote
        E.exhausted = V0  # track non-transferable votes

        E.logAction('begin', 'Begin Count')
        while True:

            #  elect candidates with quota [47]
            #
            for c in [c for c in C.hopeful(order='vote', reverse=True) if hasQuota(c)]:
                c.elect(pending=True)      # elect with surplus transfer pending
            if countComplete():
                break

            E.newRound()

            #  calculate surplus for reporting
            #
            E.surplus = sum([c.surplus for c in C.pending()], V0)

            #  transfer surplus votes of candidate with largest surplus [48,49]
            #
            if C.pending():
                high_vote = max(c.vote for c in C.pending())
                high_candidates = [c for c in C.pending() if c.vote == high_vote]
                high_candidate = breakTie(high_candidates, 'largest surplus')
                high_candidate.unpend('Transfer high surplus')
                surplus = high_candidate.vote - E.quota
                for b in (b for b in E.ballots if b.topRank == high_candidate.cid):
                    # see http://www.votingmatters.org.uk/RES/eSTV-Eval.pdf section 7.1 #5
                    b.weight = V.muldiv(b.weight, surplus, high_candidate.vote, round='down')
                    transfer(b)
                high_candidate.vote = E.quota
                E.logAction('transfer', "Surplus transferred: %s (%s)" % (high_candidate, surplus))
                continue  # to next stage/round

            #  defeat candidate(s) with lowest vote [50,51]
            #
            if C.hopeful():
                low_vote = min(c.vote for c in C.hopeful())
                low_candidates = [c for c in C.hopeful() if c.vote == low_vote]
                low_candidate = breakTie(low_candidates, 'defeat low candidate')
                low_candidate.defeat('Defeat low candidate')
                for b in (b for b in E.ballots if b.topRank == low_candidate.cid):
                    transfer(b)
                low_candidate.vote = V0
                E.logAction('transfer', "Transfer defeated: %s" % low_candidate)

            if countComplete():
                break

        #  Count complete.

        #  Finalize any elected transfer-pending candidates
        for c in C.pending():
            c.unpend()
        
        #  Fill any remaining seats [52]
        #
        if len(C.hopeful()) <= E.seatsLeftToFill():
            for c in C.hopeful():
                c.elect('Elect remaining candidates')

        #  Defeat remaining hopeful candidates for reporting purposes
        #
        for c in C.hopeful():
            c.defeat(msg='Defeat remaining candidates')
