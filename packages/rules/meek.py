'''
Count election using Reference Meek or Warren STV

copyright 2010 by Jonathan Lundell
'''

import sys

class Rule(object):
    '''
    Rule for counting Model Meek or Warren elections
    
    Parameter: arithmetic type
    '''
    
    omega = None     # epsilon for terminating iteration
    _o = None        # omega = 1/10^o

    @classmethod
    def options(cls, options=dict()):
        "filter options"
        
        #  set defaults
        #
        if options.get('rule') == 'warren':
            variant = 'warren'
        else:
            variant = options.get('variant', 'meek').lower()
            if variant not in ['meek', 'warren']:
                raise ValueError('unknown  %s; use Meek or Warren' % variant)
        cls.warren = (variant == 'warren')
        if not options.get('arithmetic'):
            options['arithmetic'] = 'quasi-exact'
        cls._o = options.get('omega', None)
        return options

    @classmethod
    def info(cls):
        "return an info string for the election report"
        name = "Warren" if cls.warren else "Meek"
        return "%s Reference (omega = 1/10^%d)" % (name, cls._o)

    @classmethod
    def reportMode(cls):
        "how should this election be reported? meek or wigm"
        return 'meek'

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
        def countComplete():
            "test for end of count"
            return C.nHopeful <= E.seatsLeftToFill() or E.seatsLeftToFill() <= 0

        def hasQuota(E, candidate):
            '''
            Determine whether a candidate has a quota (ie, is elected).
            
            If using exact arithmetic, then: vote > quota
            Otherwise: vote >= quota, since quota has been rounded up
            '''
            if E.V.exact:
                return candidate.vote > E.R.quota
            return candidate.vote >= E.R.quota
    
        def calcQuota(E):
            '''
            Calculate quota.
            
            Round up if not using exact arithmetic.
            '''
            if E.V.exact:
                return E.R.votes / E.V(E.electionProfile.nSeats+1)
            return E.R.votes / E.V(E.electionProfile.nSeats+1) + E.V.epsilon
    
        def breakTie(E, tied, purpose=None, strong=True):
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
                R.log(s)
                return t

        def batchDefeat(surplus):
            "find a batch of candidates that can be defeated at the current surplus"
            
            #   get a sorted list of candidates
            #   copy to a new list,
            #   making each entry a list
            #   where each list has tied candidates, if any
            #
            sortedCands = C.sortByVote(C.hopeful)
            group = []
            sortedGroups = []
            vote = V0
            for c in sortedCands:
                if V.equal_within(c.vote, vote, cls.omega):
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
            vote = V0
            batch = []
            maxDefeat = C.nHopeful - E.seatsLeftToFill()
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
        IS_omega = 1
        IS_batch = 2
        IS_elected = 3
        IS_stable = 4

        def iterate():
            "Iterate until surplus is sufficiently low"
            iStatus = IS_none
            lastsurplus = V(E.nBallots)
            while True:
                if V.exact:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                #
                #  distribute vote for each ballot
                #  and add up vote for each candidate
                #
                for c in C.hopefulOrElected:
                    c.vote = V0
                R.residual = V0
                for b in R.ballots:
                    b.weight = V1
                    b.residual = V(b.multiplier)
                    if cls.warren:
                        for c in b.ranking:
                            keep = c.kf if c.kf < b.residual else b.residual
                            b.weight -= keep
                            c.vote += keep * b.multiplier      # b.multiplier is an int
                            b.residual -= keep * b.multiplier  # residual value of ballot
                            if b.weight <= V0:
                                break
                    else: # meek
                        for c in b.ranking:
                            if True:
                                #
                                #  OpenSTV MeekSTV
                                #
                                #  kv = w*kf*m rounded down     keep vote
                                #  w = w*(1-kf) rounded down    new weight
                                #
                                kv = V.mul(b.weight*b.multiplier, c.kf, round='down')
                                c.vote += kv
                                b.weight = V.mul(b.weight, V1-c.kf, round='down')
                            if False:
                                #
                                #  Hill/NZ Calculator
                                #
                                #  kv = w*kf rounded up * m     keep vote
                                #  w -= w*kf rounded up         new weight
                                # 
                                kw = V.mul(b.weight, c.kf, round='up')  # keep weight
                                kv = kw * b.multiplier  # exact
                                c.vote += kv
                                b.weight -= kw
                            if False:
                                #
                                #  NZ Schedule 1A
                                #
                                #  kv = w*kf rounded up * m     keep vote
                                #  w = w*(1-kf) rounded up      new weight
                                # 
                                kv = V.mul(b.weight, c.kf, round='up') * b.multiplier  # exact
                                c.vote += kv
                                b.weight = V.mul(b.weight, V1-c.kf, round='up')
                                
                            b.residual -= kv  # residual value of ballot
                            #
                            if b.weight <= V0:
                                break
                    R.residual += b.residual  # residual for round
                R.votes = V0
                for c in C.hopefulOrElected:
                    R.votes += c.vote            # find sum of all votes

                #  D.3. update quota
                #
                R.quota = calcQuota(E)
                
                #  D.4. find winners
                #
                for c in [c for c in C.hopeful if hasQuota(E, c)]:
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
                surplus = V0
                for c in C.elected:
                    surplus += c.vote - R.quota
                R.surplus = surplus # for reporting
                
                #  D.7. test iteration complete
                #
                if surplus <= Rule.omega:
                    return IS_omega, None
                if surplus >= lastsurplus:
                    R.log("Stable state detected (%s)" % surplus) # move to caller?
                    return IS_stable, None
                lastsurplus = surplus
                batch = batchDefeat(surplus)
                if batch:
                    return IS_batch, batch
                    
                #  D.8. update keep factors
                #
                #  rounding options for non-exact arithmetic:
                #
                #  kf * quota    / vote
                #     full         up        OpenSTV MeekSTV
                #      up          up        Hill & NZ Calculator & NZ Schedule 1A
                #
                for c in C.elected:
                    c.kf = V.muldiv(c.kf, R.quota, c.vote, round='up')  # OpenSTV variant
                    #c.kf = V.div(V.mul(c.kf, R.quota, round='up'), c.vote, round='up')  # NZ variant
            
        #########################
        #
        #   Initialize Count
        #
        #########################
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one

        #  set omega
        #
        #  omega will be 1/10**o
        #
        assert V.name in ('rational', 'quasi-exact', 'fixed')
        if not cls._o:
            if V.name == 'rational':
                cls._o = 10
            elif V.name == 'quasi-exact':
                cls._o = V.precision * 2 // 3
            else: # fixed
                cls._o = V.precision * 2 // 3
        cls.omega = V(1) / V(10**cls._o)

        E.R0.votes = V(E.electionProfile.nBallots)
        E.R0.quota = calcQuota(E)
        R = E.R0
        C = R.C   # candidate state
        for c in E.withdrawn:
            c.kf = V0
        for c in C.hopeful:
            c.kf = V1    # initialize keep factors
            c.vote = V0  # initialize round-0 vote
        for b in R.ballots:
            if b.topCand:
                b.topCand.vote += V(b.multiplier)  # count first-place votes for round 0 reporting

        while not countComplete():

            #  B. next round
            #
            R = E.newRound()
            if V.exact:
                sys.stdout.write('%d' % R.n)
                sys.stdout.flush()
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
                    c.kf = V0
                    c.vote = V0
                continue

            #  Otherwise find and defeat candidate with lowest vote
            #
            low_vote = R.quota
            low_candidates = []
            for c in C.hopeful:
                if V.equal_within(c.vote, low_vote, cls.omega):
                    low_candidates.append(c)
                elif c.vote < low_vote:
                    low_vote = c.vote
                    low_candidates = [c]

            #  defeat candidate with lowest vote
            #
            if low_candidates:
                low_candidate = breakTie(E, low_candidates, 'defeat')
                C.defeat(low_candidate, msg='Defeat (surplus %s < omega)' % V(R.surplus))
                low_candidate.kf = V0
                low_candidate.vote = V0
        
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful.copy():
            if C.nElected < E.electionProfile.nSeats:
                C.elect(c, msg='Elect remaining')
            else:
                C.defeat(c, msg='Defeat remaining')
                c.kf = V0
                c.vote = V0
