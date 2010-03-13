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
        e = Election(Rule, precision=4, guard=0)
        return e

    @staticmethod
    def info(e):
        "return an info string for the election report"
        return "Minneapolis MN STV"

    #########################
    #
    #   Main Election Counter
    #
    #########################
    @staticmethod
    def count(e):
        "count the election"
        
        #  local support functions
        #
        def hasQuota(e, candidate):
            '''
            Determine whether a candidate has a quota. [167.70]
            '''
            return candidate.vote >= R.quota
    
        def calcQuota(e):
            '''
            Calculate quota. [167.20]
            '''
            return V(e.profile.nballots) / V(e.profile.nseats+1) + V(1)
        
        def breakTie(e, tied, purpose=None, strong=True):
            '''
            break a tie by lot [167.70(1)(e)]
            
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
        e.R0.quota = calcQuota(e)
        R = e.R0  # current round
        C = R.C   # candidate state
        V = e.V   # arithmetic value class
        
        #  Initialize the random number generator
        #
        random.seed(e.profile.nballots + e.profile.nseats)
        
        #  Count votes in round 0 for reporting purposes only
        #
        for c in C.hopeful:
            c.vote = V(0)
        for b in [b for b in R.ballots if not b.exhausted]:
            b.top.vote = b.top.vote + b.vote

        while C.nHopefulOrElected > e.profile.nseats and \
               C.nElected < e.profile.nseats:
            R = e.newRound()
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
            for c in [c for c in C.hopeful if hasQuota(e, c)]:
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
                high_candidate = breakTie(e, high_candidates, 'surplus')
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
                    low_candidate = breakTie(e, low_candidates, 'defeat')
                    C.defeat(low_candidate)
                    R.advance(low_candidate)
        
        #  Election over.
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.pending:
            C.unpend(c)
        for c in C.hopeful.copy():
            if C.nElected < e.profile.nseats:
                C.elect(c, msg='Elect remaining', pending=False)
            else:
                C.defeat(c, msg='Defeat remaining')
    

