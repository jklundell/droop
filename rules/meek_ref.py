#!/usr/bin/env python
"Count election using Reference Meek STV"

import sys, os, operator
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))
from modules.election import Election

class Rule:
    '''
    Rule for counting Model Meek elections
    
    Parameter: arithmetic type
    '''
    
    @staticmethod
    def init(arithmetic=None, precision=6, guard=None):
        "initialize election parameters"
        
        #  set defaults
        #
        if arithmetic is None: arithmetic = 'fixed'
        if arithmetic == 'rational':
            precision = guard = None
        elif arithmetic == 'qx':
            if precision is None:
                precision = 9
                guard = None
        elif precision == 'fixed':
            if precision is None: precision = 9
            guard = 0
        elif arithmetic == 'integer':
            precision = guard = 0
        else:
            raise TypeError('unrecognized arithmetic type (%s)' % arithmetic)

        #  create an election
        #
        e = Election(Rule, precision, guard)

        #  set epsilon
        #
        Rule.epsilon = e.V.epsilon
        return e

    @staticmethod
    def info(e):
        "return an info string for the election report"
        return "Model Meek"

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
        def seatsLeftToFill():
            "number of seats not yet filled"
            return e.profile.nseats - C.nElected

        def countComplete():
            "test for end of count"
            return C.nHopeful <= seatsLeftToFill() or seatsLeftToFill() <= 0

        def hasQuota(e, candidate):
            '''
            Determine whether a candidate has a quota (ie, is elected).
            
            If using exact arithmetic, then: vote > quota
            Otherwise: vote >= quota, since quota has been rounded up
            '''
            if e.V.exact:
                return candidate.vote > e.R.quota
            return candidate.vote >= e.R.quota
    
        def calcQuota(e):
            '''
            Calculate quota.
            
            Round up if not using exact arithmetic.
            '''
            if e.V.exact:
                return e.V(e.profile.nballots) / e.V(e.profile.nseats+1)
            return e.V(e.profile.nballots) / e.V(e.profile.nseats+1) + e.V.epsilon
    
        def breakTie(e, tied, purpose=None, strong=True):
            '''
            break a tie
            
            purpose must be 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to eliminate. 
            
            Set strong to False to indicate that weak tiebreaking should be
            attempted, if relevant. Otherwise the tie is treated as strong.
            
            Not all tiebreaking methods will care about 'purpose' or 'strength',
            but the requirement is enforced for consistency of interface.
            '''
            assert purpose in ('surplus', 'elect', 'defeat')
            if not tied:
                return None
            if len(tied) == 1:
                return tied[0]
            if len(tied) > 1:
                t = tied[0]  # TODO: real tiebreaker
                s = 'Break tie (%s): [' % purpose
                s += ", ".join([c.name for c in tied])
                s += '] -> %s' % t.name
                e.R.log(s)
                return t

        def batchDefeat(surplus):
            "find a batch of candidates that can be defeated at the current surplus"
            
            sortedCands = sorted(C.hopeful, key=lambda c: c.vote)
            tiedGroups = []
            tiedCands = []
            vote = e.V(0)
            for c in sortedCands:
                if c.vote == vote:
                    tiedCands.append(c)
                else:
                    if tiedCands:
                        tiedGroups.append(tiedCands)
                    tiedcands = [c]
                    vote = c.vote
            if tiedCands:
                tiedGroups.append(tiedCands)
            vote = e.V(0)
            batch = []
            for tiedCands in tiedGroups:
                if (len(batch) + len(tiedCands)) > seatsLeftToFill():
                    break
                for c in tiedCands:
                    vote += c.vote
                if vote >= surplus:
                    break
                batch += tiedCands
            return batch

        #  Calculate initial quota
        #
        e.R0.quota = calcQuota(e)
        R = e.R0
        C = R.C   # candidate state
        for c in C.hopeful:
            c.kf = e.V(1)  # initialize keep factors

        while not countComplete():

            #  B. next round
            #
            R = e.newRound()
            C = R.C   # candidate state
            elected = False # candidate elected in this round

            #  C. iterate
            #
            while not countComplete():
                for c in C.hopefulOrElected:
                    c.vote = e.V(0)
                for b in R.ballots:
                    b.weight = e.V(1)
                    for c in [C.candidateByNick(nick) for nick in b.ranks]:
                        keep = b.weight * c.kf
                        c.vote += keep * b.count
                        b.weight -= keep
                votes = e.V(0)
                for c in C.hopefulOrElected:
                    votes += c.vote            # find sum of all votes
                    
                #  C.2. update quota
                #
                e.R.quota = calcQuota(e)
                
                #  C.3. find winners
                #
                for c in [c for c in C.hopeful if hasQuota(e, c)]:
                    c.elect()
                    elected = True
                    
                    #  C.4. test for election complete
                    #
                    if countComplete():
                        continue
    
                #  C.5. calculate total surplus
                #
                surplus = e.V(0)
                for c in C.elected:
                    surplus += c.vote - e.R.quota
                
                #  C.6. test iteration complete
                #
                batch = batchDefeat(surplus)
                if surplus <= Rule.epsilon:
                    break
                    
                #  C.7. update keep factors
                #
                for c in C.elected:
                    c.kf = (c.kf * e.R.quota) / c.vote
                
            #  D. defeat candidate
            #
            #     next round if this round elected a candidate
            #
            if elected or countComplete():
                continue
            
            if batch:
                for c in batch:
                    c.defeat(msg='Batch defeat')
            else:
                #  find and defeat candidate with lowest vote
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
                    low_candidate.defeat()
        
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful:
            if C.nElected < e.profile.nseats:
                c.elect(msg='Elect remaining')
            else:
                c.defeat(msg='Defeat remaining')
