#!/usr/bin/env python
'''
Count election using Minneapolis MN STV rules

Minneapolis Code of Ordinances, Title 8.5, Chapter 167
http://library1.municode.com/default-test/DocView/11490/1/107/109
as of 2009-10-02

Minneapolis STV is a variation on WIGM,
using fixed-point decimal arithmetic with four digits of precision.
'''

import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))
from modules.election import Election
import random

class Rule:
    '''
    Rule for counting Minneapolis MN STV
    '''
    
    @staticmethod
    def init():
        "initialize election parameters"
        
        #  create an election
        #
        #  arithmetic is fixed decimal, four digits of precision (167.20)
        #  
        #
        E = Election(Rule, precision=4, guard=0)
        return E

    @staticmethod
    def info(E):
        "return an info string for the election report"
        return "Minneapolis MN STV"

    #########################
    #
    #   Main Election Counter
    #
    #########################
    @staticmethod
    def count(E):
        "count the election"
        
        #  local support functions
        #
        def hasQuota(E, candidate):
            '''
            Determine whether a candidate has a quota. [167.70]
            '''
            return candidate.vote >= R.quota
    
        def calcQuota(E):
            '''
            Calculate quota. [167.20]
            '''
            return V(E.profile.nballots) / V(E.profile.nseats+1) + V(1)
        
        def breakTie(E, tied, purpose=None, strong=True):
            '''
            break a tie by lot [167.70(1)(E)]
            
            purpose must be 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to eliminate. 
            '''
            assert purpose in ('surplus', 'elect', 'defeat')
            if not tied:
                return None
            return random.choice(tied)

        #  Calculate quota
        #
        E.R0.quota = calcQuota(E)
        R = E.R0  # current round
        C = R.C   # candidate state
        V = E.V   # arithmetic value class
        
        #  Initialize the random number generator
        #
        random.seed(E.profile.nballots + E.profile.nseats)
        
        while True:
        
            ##  167.70(1)(a)
            ##  a. The number of votes cast for each candidate for the current round 
            ##     must be counted.
            ##
            for c in C.hopeful: c.vote = V(0)
            for b in [b for b in R.ballots if not b.exhausted]:
                b.top.vote = b.top.vote + b.vote

            ##     If the number of candidates whose vote total is equal to or greater than
            ##     the threshold is equal to the number of seats to be filled, 
            ##     those candidates who are continuing candidates are elected 
            ##     and the tabulation is complete. 
            ##

            if len([c for c in C.hopeful if hasQuota(E, c)]):
                C.elect(c, pending=True)  # elect with transfer pending
            if C.nElected >= E.profile.nseats:
                break

            ##     If the number of candidates whose vote total is equal to or greater than
            ##     the threshold is not equal to the number of seats to be filled, 
            ##     a new round begins and the tabulation must continue as described in clause b.

            R = E.newRound()

            ##  167.70(1)(b)
            ##  b. Surplus votes for any candidates whose vote total is equal to 
            ##     or greater than the threshold must be calculated.

            surplus = V(0)
            for c in C.elected:
                surplus += c.vote

            ##  167.70(1)(c)
            ##  c. After any surplus votes are calculated but not yet transferred, 
            ##     all candidates for whom it is mathematically impossible to be elected 
            ##     must be defeated simultaneously. 
            ##     Votes for the defeated candidates must be transferred to each ballot's 
            ##     next-ranked continuing candidate. 

            sureLosers = findSureLosers()
            for c in sureLosers:
                C.defeat(c)
                R.advance(c)

            ##     If no candidate can be defeated mathematically, the tabulation must continue
            ##     as described in clause d. 
            ##     Otherwise, the tabulation must continue as described in clause a.
            if sureLosers:
                continue

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
            ##     as described in clause E. 
            ##     Otherwise, the tabulation must continue as described in clause a.

            ##  E. If there are no transferable surplus votes, the candidate with the fewest votes is defeated. Votes for a defeated candidate are transferred at their transfer value to each ballot's next-ranked continuing candidate. Ties between candidates with the fewest votes must be decided by lot, and the candidate chosen by lot must be defeated. The result of the tie resolution must be recorded and reused in the event of a recount.

            ##  f. The procedures in clauses a. to E. must be repeated until the number of candidates whose vote total is equal to or greater than the threshold is equal to the number of seats to be filled, or until the number of continuing candidates is equal to the number of offices yet to be elected. If the number of continuing candidates is equal to the number of offices yet to be elected, any remaining continuing candidates must be declared elected. In the case of a tie between two (2) continuing candidates, the tie must be decided by lot as provided in Minneapolis Charter Chapter 2, Section 12, and the candidate chosen by lot must be defeated. The result of the tie resolution must be recorded and reused in the event of a recount.

                if c.vote == R.quota:     # handle new winners with no surplus
                    R.advance(c)
                    C.unpend(c)



            C.nHopefulOrElected > E.profile.nseats and \
               C.nElected < E.profile.nseats:



            C = R.C   # candidate state

            #  count votes for hopeful candidates [167.70(1)(a)]
            #
            for c in C.hopefulOrPending:
                c.vote = V(0)
            for b in [b for b in R.ballots if not b.exhausted]:
                b.top.vote = b.top.vote + b.vote

            #  calculate surplus [167.70(1)(b)
            
            #  defeat sure losers [167.70(1)(c)]
            #     and next round if any


            #  elect new winners
            #
            for c in [c for c in C.hopeful if hasQuota(E, c)]:
                C.elect(c, pending=True)  # elect with transfer pending
                if c.vote == R.quota:     # handle new winners with no surplus
                    R.advance(c)
                    C.unpend(c)
        
            #  find highest surplus
            #
            high_vote = R.quota
            high_candidates = []
            for c in C.elected:
                if c.vote == high_vote:
                    high_candidates.append(c)
                elif c.vote > high_vote:
                    high_vote = c.vote
                    high_candidates = [c]
            
            # transfer highest surplus
            #
            if high_vote > R.quota:
                # transfer surplus
                high_candidate = breakTie(E, high_candidates, 'surplus')
                surplus = high_vote - R.quota
                for b in [b for b in R.ballots if b.top == high_candidate]:
                    b.weight = (b.weight * surplus) / high_vote
                R.advance(high_candidate)
                C.unpend(high_candidate)
                high_candidate.vote = R.quota

            #  if no surplus to transfer, eliminate a candidate
            #
            else:
                #  find candidate(s) with lowest vote
                #
                low_vote = R.quota
                low_candidates = []
                for c in C.hopeful:
                    if c.vote == low_vote:
                        low_candidates.append(c)
                    elif c.vote < low_vote:
                        low_vote = c.vote
                        low_candidates = [c]

                #  defeat candidate with lowest vote
                #
                if low_candidates:
                    low_candidate = breakTie(E, low_candidates, 'defeat')
                    C.defeat(low_candidate)
                    R.advance(low_candidate)
        
        #  Election over.
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.pending:
            C.unpend(c)
        for c in C.hopeful.copy():
            if C.nElected < E.profile.nseats:
                C.elect(c, msg='Elect remaining', pending=False)
            else:
                C.defeat(c, msg='Defeat remaining')
    

