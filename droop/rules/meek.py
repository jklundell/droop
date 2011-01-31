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

from __future__ import absolute_import
from .electionmethods import MethodMeek

class Rule(MethodMeek):
    '''
    Rule for counting Model Meek or Warren elections
    
    Parameter: arithmetic type
    '''
    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return ('meek', 'warren')

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
        
    def __init__(self, E):
        "initialize rule"
        self.E = E
        self.name = None
        self.warren = False
        self.omega = None
        self.omega10 = None
        self.defeat_batch = None

    def options(self):
        "Meek options"
        self.name = self.E.options.getopt('rule')
        self.warren = self.name == 'warren'
        options = self.E.options

        arithmetic = options.setopt('arithmetic', default='guarded')
        if arithmetic == 'guarded':
            precision = options.setopt('precision', default=18)
            options.setopt('guard', default=precision//2)
            self.omega10 = options.setopt('omega', default=precision//2)
        elif arithmetic == 'fixed':
            precision = options.setopt('precision', default=9)
            self.omega10 = options.setopt('omega', default=precision*2//3)
        elif arithmetic == 'rational':
            self.omega10 = options.setopt('omega', default=10)

        self.defeat_batch = options.setopt('defeat_batch', default='safe', allowed=('none','safe'))

    def info(self):
        "return an info string for the election report"
        name = "Warren" if self.warren else "Meek"
        return "%s Parametric (omega = 1/10^%d)" % (name, self.omega10)

    def tag(self):
        "return a tag string for unit tests"
        if self.warren:
            return 'warren-o%s' % self.omega10
        return 'meek-o%s' % self.omega10

    #########################
    #
    #   Main Election Counter
    #
    #########################
    def count(self):
        "count the election"
        
        #  local support functions
        #
        def countComplete():
            "test for end of count"
            return len(C.hopeful()) <= E.seatsLeftToFill() or E.seatsLeftToFill() <= 0

        def hasQuota(candidate):
            '''
            Determine whether a candidate has a quota (ie, is elected).
            
            If using exact arithmetic, then: vote > quota
            Otherwise: vote >= quota, since quota has been rounded up
            '''
            if E.V.exact:
                return candidate.vote > E.quota
            return candidate.vote >= E.quota
    
        def calcQuota():
            '''
            Calculate quota.
            
            Round up if not using exact arithmetic.
            '''
            if E.V.exact:
                return E.votes / E.V(E.nSeats+1)
            return E.votes / E.V(E.nSeats+1) + E.V.epsilon
    
        def breakTie(E, tied, reason=None):
            '''
            break a tie
            
            reason is 'surplus' or 'elect' or 'defeat', 
            indicating whether the tie is being broken for the purpose 
            of choosing a surplus to transfer, a winner, 
            or a candidate to defeat. 
            
            the tiebreaking method: candidates are randomly ordered,
            and the order of entry in the ballot file 
            or the profile =tie order is the tiebreaking order:
            choose the first candidate in that order.
            '''
            if len(tied) == 1:
                return tied.pop()
            t = C.byTieOrder(tied)[0]
            names =  ", ".join([c.name for c in tied])
            E.logAction('tie', 'Break tie (%s): [%s] -> %s' % (reason, names, t))
            return t

        def batchDefeat(surplus):
            "find a batch of candidates that can be defeated at the current surplus"
            
            if self.defeat_batch == 'none':
                return []
                
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

        #  iterateStatus constants: why did the iteration terminate?
        #
        IS_none = 'none'
        IS_omega = 'omega'
        IS_batch = 'batch'
        IS_elected = 'elected'
        IS_stable = 'stable'

        def distributeVotes():
            "perform a Meek/Warren distribution of votes on all ballots"

            def kw_warren(kf, weight):
                "calculate keep and new weight for Warren"
                keep = kf if kf < weight else weight
                return (kf if kf < weight else weight), (weight - keep)
                
            def kw_meekOpenSTV(kf, weight):
                "calculate keep and new weight for OpenSTV MeekSTV"
                return V.mul(weight, kf, round='down'), V.mul(weight, V1-kf, round='down')
        
            def kw_meekHill(kf, weight):    # pragma: no cover  # pylint: disable=W0612
                "calculate keep and new weight for Hill/NZ Calculator"
                keep = V.mul(weight, kf, round='up')
                return keep, (weight - keep)
        
            def kw_meekNZ1A(kf, weight):    # pragma: no cover  # pylint: disable=W0612
                "calculate keep and new weight for NZ Schedule 1A"
                return V.mul(weight, kf, round='up'), V.mul(weight, V1-kf, round='up')

            kt = kw_warren if self.warren else kw_meekOpenSTV
            
            for c in (C.hopeful() + C.elected()):
                c.vote = V0
            candidate = E.candidate
            E.residual = V0
            for b in E.ballots:
                multiplier = b.multiplier
                b.residual = multiplier
                b.weight = V1
                for c in (candidate(cid) for cid in b.ranking):
                    if c.kf:
                        keep, b.weight = kt(c.kf, b.weight)
                        c.vote += keep * multiplier
                        b.residual -= keep * multiplier  # residual value of ballot
                        if b.weight <= V0:
                            break
                E.residual += b.residual  # residual for round
                
            for b in E.ballotsEqual:
                cset = [c.cid for c in (C.hopeful() + C.elected())]
                nrank = len(b.ranking)
                multiplier = b.multiplier
                b.residual = multiplier

                def dist(i, weight):
                    "distribute via recursive descent"
                    cids = [cid for cid in b.ranking[i] if cid in cset]
                    if cids:
                        cweight = weight / V(len(cids))
                        for cid in cids:
                            c = candidate(cid)
                            keep, weight = kt(c.kf, cweight)
                            c.vote += keep * multiplier
                            b.residual -= keep * multiplier  # residual value of ballot
                            if weight and i < nrank:
                                dist(i+1, weight)

                dist(0, V1)
                E.residual += b.residual  # residual for round

        def iterate():
            "Iterate until surplus is sufficiently low"

            iStatus = IS_none
            lastsurplus = V(E.nBallots)
            while True:
                if V.exact:
                    E.prog('.')
                #
                #  distribute vote for each ballot
                #  and add up vote for each candidate
                #
                distributeVotes()
                E.votes = sum([c.vote for c in (C.hopeful() + C.elected())], V0)

                #  D.3. update quota
                #
                E.quota = calcQuota()
                
                #  D.4. find winners
                #
                for c in [c for c in C.hopeful() if hasQuota(c)]:
                    c.elect()
                    iStatus = IS_elected
                    
                #  D.6. calculate total surplus
                #
                E.surplus = sum([c.vote-E.quota for c in C.elected()], V0)
                
                #  D.7. test iteration complete
                #
                #  case 1: a candidate was elected
                #  case 2: surplus < omega
                #  case 3: surplus stable (not decreasing)
                #  case 4: there are sure losers to defeat
                #
                if iStatus == IS_elected:
                    return IS_elected, None
                if E.surplus <= self.omega:
                    return IS_omega, None
                if E.surplus >= lastsurplus:
                    E.log("Stable state detected (%s)" % E.surplus)
                    return IS_stable, None
                batch = batchDefeat(E.surplus)
                if batch:
                    return IS_batch, batch
                lastsurplus = E.surplus

                #  D.8. update keep factors
                #
                #  rounding options for non-exact arithmetic:
                #
                #  kf * quota    / vote
                #     full         up        OpenSTV MeekSTV
                #      up          up        Hill & NZ Calculator & NZ Schedule 1A
                #
                for c in C.elected():
                    #c.kf = V.muldiv(c.kf, E.quota, c.vote, round='up')  # OpenSTV variant
                    c.kf = V.div(V.mul(c.kf, E.quota, round='up'), c.vote, round='up')  # NZ variant
            
        #########################
        #
        #   Initialize Count
        #
        #########################
        E = self.E
        V = E.V    # arithmetic value class
        V0 = E.V0  # constant zero
        V1 = E.V1  # constant one

        #  set omega
        #
        #  omega will be 1/10**omega10
        #
        assert V.name in ('rational', 'guarded', 'fixed')
        self.omega10 = int(self.omega10)
        self.omega = V1 / V(10**self.omega10)

        E.votes = V(E.nBallots)
        E.quota = calcQuota()
        C = E.C   # candidates
        for c in C.hopeful():
            c.kf = V1    # initialize keep factors
        for b in (b for b in E.ballots if b.topCand): # count first-place votes for round 0 reporting
            b.topCand.vote += b.multiplier

        #  count votes from ballots with equal rankings
        #
        for b in E.ballotsEqual:
            v = (V1 // V(len(b.topRank))) * b.multiplier
            for cid in b.topRank:
                E.candidate(cid).vote += v

        E.logAction('begin', 'Begin Count')
        while not countComplete():

            #  B. next round
            #
            E.newRound()
            if V.exact:
                E.prog('%d' % E.round)

            #  C. iterate
            #     next round if iteration elected a candidate
            #
            iterationStatus, batch = iterate()
            E.logAction('iterate', 'Iterate (%s)' % iterationStatus)
            if iterationStatus == IS_elected:
                continue

            #  D. defeat candidate(s)
            #
            #     defeat a batch if possible
            #
            if iterationStatus == IS_batch:
                for c in C.byBallotOrder(batch):
                    c.defeat(msg='Defeat certain loser')
                    c.kf = V0
                    c.vote = V0
                    distributeVotes()  # for reporting
                continue

            #  find candidate(s) within surplus of lowest vote (effectively tied)
            #  defeat candidate with lowest vote, breaking tie if necessary
            #
            if C.hopeful():
                low_vote = V.min([c.vote for c in C.hopeful()])
                low_candidates = [c for c in C.hopeful() if (low_vote + E.surplus) >= c.vote]
                low_candidate = breakTie(E, low_candidates, 'defeat')
                if iterationStatus == IS_omega:
                    low_candidate.defeat(msg='Defeat (surplus %s < omega)' % E.surplus)
                else:
                    low_candidate.defeat(msg='Defeat (stable surplus %s)' % E.surplus)
                low_candidate.kf = V0
                low_candidate.vote = V0
                distributeVotes()  # for reporting
        
        #  Elect or defeat remaining hopeful candidates
        #
        for c in C.hopeful():
            if len(C.elected()) < E.electionProfile.nSeats:
                c.elect(msg='Elect remaining')
            else:
                c.defeat(msg='Defeat remaining')
                c.kf = V0
                c.vote = V0
            distributeVotes()  # for reporting

        #  final vote count for reporting
        E.votes = sum([c.vote for c in C.elected()], V0)
        E.residual = V(E.nBallots) - E.votes
