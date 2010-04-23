'''
Count election using Reference Meek or Warren STV

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

class Rule(ElectionRule):
    '''
    Rule for counting Model Meek or Warren elections
    
    Parameter: arithmetic type
    '''
    
    omega = None          # in digits
    defeatBatch = None    # default
    warren = False

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return ('meek', 'warren')

    @classmethod
    def tag(cls):
        "return a tag string for unit tests"
        if cls.warren:
            return 'warren-generic-o%s' % cls.omega
        return 'meek-generic-o%s' % cls.omega

    @classmethod
    def helps(cls, helps, name):
        "add help strings for meek and warren"
        h =  '%s is an iterative election rule.\n' % name
        h += '\noptions:\n'
        h += '  arithmetic: (guarded*, rational, fixed)\n'
        h += '  precision=significant precision (not counting guard) if guarded or fixed\n'
        h += '    default: 9 if fixed; 18 if guarded\n'
        h += '  guard=guard digits (guarded only)\n'
        h += '    default: precision/2\n'
        h += '  omega=iteration limit such that an interation is terminated\n'
        h += '    when surplus < 1/10^omega.\n'
        h += '    default: 10 if rational\n'
        h += '    default: precision/2 if guarded\n'
        h += '    default: 2/3 of precision if fixed\n'
        h += '  defeat_batch=(safe*, none)\n'
        h += '  * default\n'
        helps[name] = h
        
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
                raise UsageError('unknown variant %s; use meek or warren' % variant)
        cls.warren = (variant == 'warren')
        options.setdefault('arithmetic', 'guarded')
        if options['arithmetic'] == 'guarded':
            options.setdefault('precision', 18)
            options.setdefault('guard', options['precision']//2)
            cls.omega = options.get('omega', options['precision']//2)
        elif options['arithmetic'] == 'fixed':
            options.setdefault('precision', 9)
            cls.omega = options.get('omega', options['precision']*2//3)
        elif options['arithmetic'] == 'rational':
            cls.omega = options.get('omega', 10)

        cls.defeatBatch = options.get('defeat_batch', 'safe')
        if cls.defeatBatch not in ('none', 'safe'):
            raise UsageError('unknown defeat_batch %s; use none or safe' % cls.defeatBatch)
        return options

    @classmethod
    def info(cls):
        "return an info string for the election report"
        name = "Warren" if cls.warren else "Meek"
        return "%s Parametric (omega = 1/10^%d)" % (name, cls.omega)

    @classmethod
    def method(cls):
        "underlying method: meek or wigm"
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
            return CS.nHopeful <= E.seatsLeftToFill() or E.seatsLeftToFill() <= 0

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
                return E.R.votes / E.V(E.nSeats+1)
            return E.R.votes / E.V(E.nSeats+1) + E.V.epsilon
    
        def breakTie(E, tied, purpose=None, strong=True):
            '''
            break a tie
            
            purpose is 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to defeat. 
            
            the tiebreaking method: candidates are randomly ordered,
            and the order of entry in the ballot file 
            or the profile =tie order is the tiebreaking order:
            choose the first candidate in that order.
            '''
            if len(tied) == 1:
                return tied[0]
            tied = CS.sortByTieOrder(tied)
            t = tied[0]
            R.log('Break tie (%s): [%s] -> %s' % (purpose, ", ".join([c.name for c in tied]), t.name))
            return t

        def batchDefeat(surplus):
            "find a batch of candidates that can be defeated at the current surplus"
            
            if cls.defeatBatch == 'none':
                return []
                
            #   start with candidates sorted by vote
            #   build a sorted list of groups
            #     where each group cosnists of the candidates tied at that vote
            #     (when there's no tie, a group will have one candidate)
            #
            sortedCands = CS.sortByVote(CS.hopeful)
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
            maxDefeat = CS.nHopeful - E.seatsLeftToFill()
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

        #  iterateStatus constants: why did the iteration terminate?
        #
        IS_none = None
        IS_omega = 1
        IS_batch = 2
        IS_elected = 3
        IS_stable = 4

        def iterate():
            "Iterate until surplus is sufficiently low"

            def kw_warren(kf, weight):
                "calculate keep and new weight for Warren"
                return (kf if kf < weight else weight), (weight - keep)
                
            def kw_meekOpenSTV(kf, weight):
                "calculate keep and new weight for OpenSTV MeekSTV"
                return V.mul(weight, kf, round='down'), V.mul(weight, V1-kf, round='down')
        
            def kw_meekHill(kf, weight):
                "calculate keep and new weight for Hill/NZ Calculator"
                return V.mul(weight, kf, round='up'), (weight - keep)
        
            def kw_meekNZ1A(kf, weight):
                "calculate keep and new weight for NZ Schedule 1A"
                return V.mul(weight, kf, round='up'), V.mul(weight, V1-kf, round='up')

            iStatus = IS_none
            lastsurplus = V(E.nBallots)
            while True:
                if V.exact:
                    E.prog('.')
                #
                #  distribute vote for each ballot
                #  and add up vote for each candidate
                #
                for c in CS.hopefulOrElected:
                    c.vote = V0
                E.distributeVotes(kw_meekOpenSTV)
                R.votes = sum([c.vote for c in CS.hopefulOrElected], V0)

                #  D.3. update quota
                #
                R.quota = calcQuota(E)
                
                #  D.4. find winners
                #
                for c in [c for c in CS.hopeful if hasQuota(E, c)]:
                    CS.elect(c)
                    iStatus = IS_elected
                    
                #  D.6. calculate total surplus
                #
                R.surplus = sum([c.vote-R.quota for c in CS.elected], V0)
                
                #  D.7. test iteration complete
                #
                #  case 1: a candidate was elected
                #  case 2: surplus < omega
                #  case 3: surplus stable (not decreasing)
                #  case 4: there are sure losers to defeat
                #
                if iStatus == IS_elected:
                    return IS_elected, None
                if R.surplus <= Rule._omega:
                    return IS_omega, None
                if R.surplus >= lastsurplus:
                    R.log("Stable state detected (%s)" % R.surplus)
                    return IS_stable, None
                batch = batchDefeat(R.surplus)
                if batch:
                    return IS_batch, batch
                lastsurplus = R.surplus

                #  D.8. update keep factors
                #
                #  rounding options for non-exact arithmetic:
                #
                #  kf * quota    / vote
                #     full         up        OpenSTV MeekSTV
                #      up          up        Hill & NZ Calculator & NZ Schedule 1A
                #
                for c in CS.elected:
                    #c.kf = V.muldiv(c.kf, R.quota, c.vote, round='up')  # OpenSTV variant
                    c.kf = V.div(V.mul(c.kf, R.quota, round='up'), c.vote, round='up')  # NZ variant
            
        #########################
        #
        #   Initialize Count
        #
        #########################
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one

        #  set _omega
        #
        #  _omega will be 1/10**omega
        #
        assert V.name in ('rational', 'guarded', 'fixed')
        cls.omega = int(cls.omega)
        cls._omega = V1 / V(10**cls.omega)

        E.R0.votes = V(E.nBallots)
        E.R0.quota = calcQuota(E)
        R = E.R0
        CS = R.CS   # candidate state
        for c in E.withdrawn:
            c.kf = V0
        for c in CS.hopeful:
            c.kf = V1    # initialize keep factors
        E.countTopVotes()  # count first-place votes for round 0 reporting

        while not countComplete():

            #  B. next round
            #
            R = E.newRound()
            if V.exact:
                E.prog('%d' % R.n)
            CS = R.CS   # candidate state

            #  CS. iterate
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
                for c in CS.sortByOrder(batch):
                    CS.defeat(c, msg='Defeat certain loser')
                    c.kf = V0
                    c.vote = V0
                continue

            #  find candidate(s) within surplus of lowest vote (effectively tied)
            #  defeat candidate with lowest vote, breaking tie if necessary
            #
            if CS.hopeful:
                low_vote = V.min([c.vote for c in CS.hopeful])
                low_candidates = [c for c in CS.hopeful if (low_vote + R.surplus) >= c.vote]
                low_candidate = breakTie(E, low_candidates, 'defeat')
                if iterationStatus == IS_omega:
                    CS.defeat(low_candidate, msg='Defeat (surplus %s < omega)' % V(R.surplus))
                else:
                    CS.defeat(low_candidate, msg='Defeat (stable surplus %s)' % V(R.surplus))
                low_candidate.kf = V0
                low_candidate.vote = V0
        
        #  Elect or defeat remaining hopeful candidates
        #
        for c in list(CS.hopeful):
            if CS.nElected < E.electionProfile.nSeats:
                CS.elect(c, msg='Elect remaining')
            else:
                CS.defeat(c, msg='Defeat remaining')
                c.kf = V0
                c.vote = V0
