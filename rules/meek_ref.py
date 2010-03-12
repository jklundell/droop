#!/usr/bin/env python
"Count election using Reference Meek STV"

import sys, os
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
        elif arithmetic == 'fixed':
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
                return e.R.votes / e.V(e.profile.nseats+1)
            return e.R.votes / e.V(e.profile.nseats+1) + e.V.epsilon
    
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
            
            #  sortedCands = candidates sorted by vote
            #
            sortedCands = sorted(C.hopeful, key=lambda c: c.vote)
            
            #   copy the sorted candidates list, 
            #   making each entry a list
            #   where each list has tied candidates, if any
            #
            group = []
            sortedGroups = []
            vote = V(0)
            for c in sortedCands:
                if c.vote == vote:
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
            #     * we leave enough hopeful candidates to fill the remaining seats
            #     * we don't break up tied groups of candidates
            #     * the total of the surplus and the votes for the defeated batch
            #       is less than the next-higher candidate
            #
            #   We never defeat the last group, because that would mean
            #   defeating all the hopeful candidates, and if that's possible,
            #   the election is already complete and we wouldn't be here.
            #   
            vote = V(0)
            batch = []
            maxDefeat = C.nHopeful - seatsLeftToFill()
            for g in range(len(sortedGroups) - 1):
                group = sortedGroups[g]
                if (len(batch) + len(group)) > maxDefeat:
                    break  # too many defeats
                vote += group[0].vote * len(group)
                if (vote + surplus) >= sortedGroups[g+1][0].vote:
                    break  # not sure losers
                batch += group
            return batch

        #  iterateStatus constants
        #
        IS_none = None
        IS_epsilon = 1
        IS_batch = 2
        IS_elected = 3
        IS_stable = 4

        def iterate():
            "Iterate until surplus is sufficiently low"
            iStatus = IS_none
            lastsurplus = V(0)
            while True:
                if V.exact:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                #
                #  distribute vote for each ballot
                #  and add up vote for each candidate
                #
                for c in C.hopefulOrElected:
                    c.vote = V(0)
                R.residual = V(0)
                for b in R.ballots:
                    b.weight = V(1)
                    b.residual = V(b.count)
                    for c in [e.candidateByCid(cid) for cid in b.ranks]:
                        keep = V.mul(b.weight, c.kf, round='up')  # Hill variation
                        b.weight -= keep  # Hill variation
                        c.vote += keep * b.count  # always exact (b.count is an integer)
                        b.residual -= keep * b.count  # residual value of ballot
                        if b.weight <= V(0):
                            break
                    R.residual += b.residual  # residual for round
                R.votes = V(0)
                for c in C.hopefulOrElected:
                    R.votes += c.vote            # find sum of all votes

                #  D.3. update quota
                #
                R.quota = calcQuota(e)
                
                #  D.4. find winners
                #
                for c in [c for c in C.hopeful if hasQuota(e, c)]:
                    C.elect(c)
                    iStatus = IS_elected
                    
                    #  D.5. test for election complete
                    #
                    #if countComplete():
                    #    return IS_complete, None
                
                if iStatus == IS_elected:
                    return IS_elected, None
    
                #  D.6. calculate total surplus
                #
                surplus = V(0)
                for c in C.elected:
                    surplus += c.vote - R.quota
                
                #  D.7. test iteration complete
                #
                if surplus <= Rule.epsilon:
                    return IS_epsilon, None
                if surplus == lastsurplus:
                    R.log("Stable state detected") # move to caller?
                    return IS_stable, None
                lastsurplus = surplus
                batch = batchDefeat(surplus)
                if batch:
                    return IS_batch, batch
                    
                #  D.8. update keep factors
                #
                #  variations:
                #  Hill: full-precision multiply, round quotient up; transfer quota-keep
                #  NZ Schedule 1A: full-precision multiply(?), round quotient up; transfer (1-kf) rounded up
                #  OpenSTV MeekStV: full-precision multiply, round quotient down; transfer (1-kf) rounded down
                #
                for c in C.elected:
                    c.kf = V.muldiv(c.kf, R.quota, c.vote, round='up')  # Hill (and NZ STV Calculator) variant
            
        #########################
        #
        #   Initialize Count
        #
        #########################
        V = e.V
        e.R0.votes = V(e.profile.nballots)
        e.R0.quota = calcQuota(e)
        R = e.R0
        C = R.C   # candidate state
        for c in e.withdrawn:
            c.kf = V(0)
        for c in C.hopeful:
            c.kf = V(1)    # initialize keep factors
            c.vote = V(0)  # initialize round-0 vote
        for b in R.ballots:
            if b.top:
                b.top.vote += V(b.count)  # count first-place votes for round 0 reporting

        while not countComplete():

            #  B. next round
            #
            R = e.newRound()
            if V.exact:
                sys.stdout.write('%d' % R.n)
                sys.stdout.flush()
                for c in C.elected:  # experimental: reset keep factors for exact methods
                    c.kf = V(1)
            C = R.C   # candidate state

            #  C. iterate
            #     next round if iteration elected a candidate
            #
            iterationStatus, batch = iterate()
            if iterationStatus == IS_elected:
                continue

            #  D. defeat candidate(s)
            #
            #     defeat a batch if possible
            #
            if iterationStatus == IS_batch:
                for c in batch:
                    C.defeat(c, msg='Defeat')
                    c.kf = V(0)
                    c.vote = V(0)
                continue

            #  Otherwise find and defeat candidate with lowest vote
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
                C.defeat(low_candidate, msg='Defeat (surplus<epsilon)')
                low_candidate.kf = V(0)
                low_candidate.vote = V(0)
        
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful.copy():
            if C.nElected < e.profile.nseats:
                C.elect(c, msg='Elect remaining')
            else:
                C.defeat(c, msg='Defeat remaining')
                c.kf = V(0)
                c.vote = V(0)
