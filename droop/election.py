# -*- coding: utf-8 -*-
'''
Generic Election Support

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

Top-level structure:

  A driver program (for example Droop.py, the CLI) 
    1. creates an ElectionProfile from a ballot file,
    2. imports a Rule, 
    3. creates an Election(Rule, ElectionProfile, options),
    4. counts the election with Election.count(), and
    5. generates a report with Election.report().
  
  The options are used to override default Rule parameters, such as arithmetic.
'''

import sys, re, copy
import values
import droop
from droop.common import ElectionError, parseOptions

class Election(object):
    '''
    container for an election
    '''
    
    def __init__(self, electionProfile, options=dict()):
        "create an election from the incoming election profile"

        #  before this, a rule has been specified and a profile created
        #
        #  sequence of operations:
        #
        #    merge options from profile
        #    find rule class
        #    convert numeric option values to ints
        #    let rule process options (set defaults, etc)
        #    initialize arithmetic class
        #    save profile
        #    build candidate objects
        #    make a tiebreaking-order, if specified
        #    make the ballots object
        #
        if not electionProfile:
            raise ElectionError('no election profile specified')

        for opt, value in parseOptions(electionProfile.options).items():
            if opt not in options:
                options[opt] = value

        rulename = options.get('rule')
        if rulename is None:
            raise ElectionError('no election rule specified')
        Rule = droop.electionRule(rulename)    # get rule class
        if Rule is None:
            raise ElectionError('unknown election rule: %s' % rulename)
        self.rule = Rule(self)

        # convert numeric options (precision, etc) to ints
        for key, value in options.iteritems():
            if isinstance(value, str) and re.match(r'\d+$', value):
                options[key] = int(value)
        self.options_all = set(options)
        self.options_used = set(('rule', 'arithmetic'))
        self.options_ignored = set()
        self.options = self.rule.options(options, self.options_used, self.options_ignored)     # allow rule to process options
        self.V = values.ArithmeticClass(self.options, self.options_used, self.options_ignored) # then set arithmetic
        self.V0 = self.V(0)  # constant zero for efficiency
        self.V1 = self.V(1)  # constant one for efficiency
        self.electionProfile = electionProfile
        self.actions = []                 # list of actions
        self.round = 0                    # round number

        #  create candidate objects for candidates in election profile
        #
        self.candidates = dict()  # cid: Candidate
        self.C = Candidates()
        for cid in sorted(electionProfile.eligible | electionProfile.withdrawn):
            c = Candidate(self, cid, electionProfile.candidateOrder(cid), 
                electionProfile.tieOrder[cid],
                electionProfile.candidateName(cid),
                electionProfile.nickName[cid],
                cid in electionProfile.withdrawn)
            self.C.add(self, c)
            self.candidates[cid] = c

        #  create a ballot object (ranking candidate IDs) from the profile rankings of candidate IDs
        #  withdrawn candidates have been removed already
        #
        self.ballots = list()
        for bl in electionProfile.ballotLines:
            if bl.ranking:  # skip if only withdrawn candidates
                self.ballots.append(self.Ballot(self, bl.multiplier, bl.ranking))
        self.ballotsEqual = list()
        for bl in electionProfile.ballotLinesEqual:
            if bl.ranking:  # skip if only withdrawn candidates
                self.ballotsEqual.append(self.Ballot(self, bl.multiplier, bl.ranking))

    def count(self):
        "count the election"
        self.quota = self.V0
        self.surplus = self.V0
        self.votes = self.V0
        if self.rule.method == 'meek':
            self.residual = self.V0
        elif self.rule.method == 'qpq':
            self.ta = self.V0
            self.tx = self.V0
        for c in self.C:
            c.vote = self.V0
        self.rule.count()   ### count the election ###
        self.logAction('final', 'Count Complete')
        self.elected = self.C.elected()

    def logAction(self, action, msg):
        "record an action"
        self.actions.append(self.Action(self, action, msg))

    def log(self, msg):
        "log a message as an action"
        self.logAction('log', msg)

    def newRound(self):
        "add a round"
        self.round += 1
        self.logAction('round', 'New Round')

    @classmethod
    def makehelp(cls):
        "build a dictionary of help strings on various subjects"
        helps = dict()
        helps['rule'] =  'available rules: %s' % ','.join(droop.electionRuleNames())
        for name in droop.electionRuleNames():
            droop.ruleByName[name].helps(helps, name)
        values.helps(helps)
        return helps

    @property
    def title(self):
        "election title"
        return self.electionProfile.title

    @property
    def nSeats(self):
        "number of seats"
        return self.electionProfile.nSeats
        
    @property
    def nBallots(self):
        "number of ballots"
        return self.electionProfile.nBallots
        
    def candidate(self, cid):
        "look up a candidate from a candidate ID"
        return self.candidates[cid]
        
    def prog(self, msg):
        "log to the console (immediate output)"
        sys.stdout.write(msg)
        sys.stdout.flush()

    def signature(self):
        "return election signature (compact form of critical actions)"
        s = ''
        for action in self.actions:
            s += action.signature()
        return s

    def report(self, intr=False):
        "report election by round:action"
        s = "\nElection: %s\n\n" % self.title
        s += "\tDroop package: %s v%s\n" % (droop.common.droopName, droop.common.droopVersion)
        s += "\tRule: %s\n" % self.rule.info()
        s += "\tArithmetic: %s\n" % self.V.info
        ignored = list()
        for opt in self.options_all:
            if opt in self.options_ignored or opt not in self.options_used:
                ignored.append(opt)
        if ignored:
            s += "\tIgnored options: %s\n" % ", ".join(ignored)
        s += "\tSeats: %d\n" % self.nSeats
        s += "\tBallots: %d\n" % self.nBallots
        s += "\tQuota: %s\n" % self.V(self.quota)
        if self.rule.method == 'meek':
            s += "\tOmega: %s\n" % self.rule._omega
        if self.electionProfile.source:
            s += "Source: %s\n" % self.electionProfile.source
        if self.electionProfile.comment:
            s += "{%s}\n" % self.electionProfile.comment
        s += '\n'
        if intr:    # pragma: no cover
            s += "\t** Count terminated prematurely by user interrupt **\n\n"
            self.log('** count interrupted; this round is incomplete **')
        s += self.V.report()
        for action in self.actions:
            s += action.report()
        return s

    def dump(self):
        "dump election by action"
        s = self.actions[0].dump(header=True)
        for action in self.actions:
            s += action.dump()
        return s

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - len(self.C.elected())

    class Action(object):
        "one action"
        
        def __init__(self, E, action, msg):
            "create an action"
            assert(action in (
                'log',      # log an arbitrary string
                'round',    # start a new round
                'tie',      # break a tie
                'elect',    # elect a candidate
                'defeat',   # defeat a candidate
                'iterate',  # terminate an iteration (meek)
                'pend',     # elect a candidate pending surplus transfer (wigm)
                'transfer', # transfer a surplus (wigm)
                'final'     # end of count
                ))
            self.E = E
            self.action = action
            self.msg = msg
            self.round = E.round
            if action == "log":
                return
            C = self.C = E.C.copy(E)    # save a copy of the Candidates state
            self.votes = sum([c.vote for c in C.eligible()], E.V0)
            self.quota = E.quota
            self.surplus = E.V(E.surplus)
            if E.rule.method == 'meek':
                self.residual = E.residual  # meek residual is the nontransferable portion
            elif E.rule.method == 'wigm':
                #
                #  this is expensive in a big election, so we've done a little optimization
                #
                self.nt_votes = sum((b.vote for b in E.ballots if b.exhausted), E.V0) # nontransferable votes
                self.h_votes = sum((c.vote for c in C.hopeful()), E.V0)     # votes for hopeful candidates
                self.e_votes = sum((c.vote for c in C.notpending()), E.V0)  # votes for elected (transfer not pending) candidates
                self.p_votes = sum((c.vote for c in C.pending()), E.V0)     # votes for elected (transfer pending) candidates
                self.d_votes = sum((c.vote for c in C.defeated()), E.V0)    # votes for defeated candidates
                total = self.e_votes + self.p_votes + self.h_votes + self.d_votes + self.nt_votes  # vote total
                self.residual = E.V(E.nBallots) - total                     # votes lost due to rounding error
            elif E.rule.method == 'qpq':
                self.votes = E.votes    # total votes
                self.ta = E.ta          # candidates elected by active ballots
                self.tx = E.tx          # candidates elected by inactive ballots
                self.surplus = '-'      # qpq has no surplus
            
        def signature(self):
            "return an action signature"

            #  dump a line of data
            #
            if self.action not in ('elect', 'defeat', 'pend', 'tie', 'final'):
                return ''
            E = self.E
            V = E.V
            candidates = self.C.eligible(order="ballot") # report in ballot order
            tag = self.action[0]
            round = 'F' if self.action == 'final' else self.round
            r = [round, tag, V(self.quota)]
            if E.rule.method == 'meek':
                r.extend([V(self.votes), V(self.surplus), V(self.residual)])
            elif E.rule.method == 'wigm':
                votes = self.e_votes + self.p_votes + self.h_votes + self.d_votes
                total = votes + self.nt_votes + self.residual
                r.extend([V(total), V(votes), V(self.nt_votes), V(self.residual)])
            elif E.rule.method == 'qpq':
                pass

            for c in candidates:
                r.append(c.nick)
                r.append(c.code())
                r.append(V(c.vote))
                if E.rule.method == 'meek': r.append(V(c.kf))

            r = [str(item) for item in r]
            return ':'.join(r) + '\n'

        def report(self):
            "report an action"
            E = self.E
            if self.action == 'log':
                return "\t%s\n" % self.msg
            s = E.rule.reportAction(self) # allow rule to override default report
            if s is not None:
                return s
            if self.action == 'round':
                return "Round %d:\n" % self.round
            V = E.V
            C = self.C
            s = 'Action: %s\n' % (self.msg)
            if self.action in ('elect', 'defeat', 'pend', 'transfer'):
                for c in C.notpending():
                    s += '\tElected:  %s (%s)\n' % (c, V(c.vote))
                for c in C.pending():
                    s += '\tPending:  %s (%s)\n' % (c, V(c.vote))
                for c in C.hopeful():
                    s += '\tHopeful:  %s (%s)\n' % (c, V(c.vote))
                for c in (c for c in C.defeated() if c.vote > E.V0):
                    s += '\tDefeated: %s (%s)\n' % (c, V(c.vote))
                c0 = [c.name for c in C.defeated() if c.vote == E.V0]
                if c0:
                    s += '\tDefeated: %s (%s)\n' % (', '.join(c0), E.V0)
            if E.rule.method == 'meek':
                s += '\tQuota: %s\n' % V(self.quota)
                s += '\tVotes: %s\n' % V(self.votes)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V((self.votes + self.residual))
                s += '\tSurplus: %s\n' % V(self.surplus)
            elif E.rule.method == 'wigm':
                s += '\tElected votes: %s\n' % V(self.e_votes)
                if self.p_votes:
                    s += '\tPending votes: %s\n' % V(self.p_votes)
                s += '\tHopeful votes: %s\n' % V(self.h_votes)
                if self.d_votes:
                    s += '\tDefeated votes: %s\n' % V(self.d_votes)
                s += '\tNontransferable votes: %s\n' % V(self.nt_votes)
                s += '\tResidual: %s\n' % V(self.residual)
                s += '\tTotal: %s\n' % V(self.e_votes + self.p_votes + self.h_votes + self.d_votes + self.nt_votes + self.residual)
                s += '\tSurplus: %s\n' % V(self.surplus)
            elif E.rule.method == 'qpq':
                s += '\tCandidates elected by active ballots: %s\n' % self.ta
                s += '\tCandidates elected by inactive ballots: %s\n' % self.tx
            return s
            
        def dump(self, header=False):
            "dump an action"

            E = self.E
            V = E.V
            C = E.C
            s = ''
            candidates = C.eligible(order="ballot") # report in ballot order
            
            #  return a header line if requested
            #
            if header:
                if E.rule.method == 'meek':
                    h = ['R', 'Quota', 'Votes', 'Surplus', 'Residual']
                elif E.rule.method == 'wigm':
                    h = ['R', 'Quota', 'Total', 'Votes', 'Non-Transferable', 'Residual']
                elif E.rule.method == 'qpq':
                    h = ['R', 'Quota']

                for c in candidates:
                    h += ['%s.name' % c.cid]
                    h += ['%s.state' % c.cid]
                    h += ['%s.vote' % c.cid]
                    if E.rule.method == 'meek': h += ['%s.kf' % c.cid]
                h = [str(item) for item in h]
                s += '\t'.join(h) + '\n'
                return s
            
            #  dump a line of data
            #
            if self.action in ('round', 'log', 'iterate'):
                r = [self.round, self.msg]
            else:
                round = 'F' if self.action == 'final' else self.round
                if E.rule.method == 'meek':
                    r = [round, V(self.quota), V(self.votes), V(self.surplus), V(self.residual)]
                elif E.rule.method == 'wigm':
                    votes = self.e_votes + self.p_votes + self.h_votes + self.d_votes
                    total = votes + self.nt_votes + self.residual
                    r = [round, V(self.quota), V(total), V(votes), V(self.nt_votes), V(self.residual)]
                elif E.rule.method == 'qpq':
                    r = [round, V(self.quota)]

                for c in candidates:
                    r.append(c.name)
                    r.append(c.code())
                    r.append(V(c.vote))
                    if E.rule.method == 'meek': r.append(V(c.kf))

            r = [str(item) for item in r]
            s += '\t'.join(r) + '\n'
            return s

    class Ballot(object):
        '''
        internal representation of one ballot
        
        The use of slots gives a more compact object, which significantly
        reduces memory requirements for large elections.
        
        Similarly, ranking, from the election profile, is an array
        of bytes or shorts (depending on candidate count), again
        for memory efficiency.
        
        The ballot multiplier comes from the election profile, and is
        a count of identical ballots.
        
        The ballot weight, initially 1, is the ballot's current weight
        after possible reduction via surplus transfers.
        '''
        
        __slots__ = ('E', 'multiplier', 'index', 'weight', 'residual', 'ranking')
        
        def __init__(self, E, multiplier=1, ranking=None):
            "create a ballot"
            self.E = E
            self.multiplier = E.V(multiplier)  # number of ballots like this
            self.index = 0                # current ranking
            self.weight = E.V1            # initial weight
            self.residual = E.V0          # untransferable weight
            self.ranking = ranking

        def advance(self):
            "advance ballot index to next-ranked candidate"
            self.index += 1

        def restart(self, weight):
            "restart a ballot (for qpq)"
            self.index = 0
            self.weight = weight
            self.residual = self.E.V0

        @property
        def exhausted(self):
            "is ballot exhausted?"
            return self.index >= len(self.ranking)    # detect end-of-ranking
        
        @property
        def topRank(self):
            "return top rank (CID or tuple), or None if exhausted"
            return self.ranking[self.index] if self.index < len(self.ranking) else None
        
        @property
        def topCand(self):
            "return top candidate, or None if exhausted"
            return self.E.candidates[self.ranking[self.index]] if self.index < len(self.ranking) else None
        
        @property
        def vote(self):
            "return total vote of this ballot"
            if self.multiplier == self.E.V1:
                return self.weight  # faster
            return self.weight * self.multiplier
            

class Candidates(set):
    '''
    all candidates
    '''
    def __init__(self):
        "new Candidates"

    def copy(self, E):
        "return a copy of ourself"
        C = Candidates()
        for c in self:
            super(Candidates, C).add(copy.copy(c))
        return C

    def add(self, E, c):
        "add a candidate"
        super(Candidates, self).add(c)
        if c.state == "withdrawn":
            E.log("Add withdrawn: %s" % c.name)
        else:
            E.log("Add eligible: %s" % c.name)

    @staticmethod
    def byBallotOrder(candidates, reverse=False):
        "sort a list of candidates by ballot order"
        return sorted(candidates, key=lambda c: c.order, reverse=reverse)

    @staticmethod
    def byVote(candidates, reverse=False):
        "sort a list of candidates by vote order"
        return sorted(candidates, key=lambda c: (c.vote, c.order), reverse=reverse)

    @staticmethod
    def byTieOrder(candidates, reverse=False):
        "sort a list of candidates by tie-break order"
        return sorted(candidates, key=lambda c: c.tieOrder, reverse=reverse)

    def select(self, state, order="none", reverse=False):
        "select and return list of candidates with specified state, optionally in specified order"
        if state == "eligible":
            candidates = [c for c in self if c.state != "withdrawn"]
        elif state == "pending":
            candidates = [c for c in self if c.state == "elected" and c.pending]
        elif state == "notpending":
            candidates = [c for c in self if c.state == "elected" and not c.pending]
        else:
            candidates = [c for c in self if c.state == state]
        if order == "none":
            return candidates
        if order == "ballot":
            return self.byBallotOrder(candidates, reverse=reverse)
        if order == "tie":
            return self.byTieOrder(candidates, reverse=reverse)
        if order == "vote":
            return self.byVote(candidates, reverse=reverse)
        raise ValueError('unknown candidate sort order: %s' % order)

    def eligible(self, order="none", reverse=False):
        "select and return list of eligible candidates, in specified order"
        return self.select("eligible", order, reverse)

    def withdrawn(self, order="none", reverse=False):
        "select and return list of eligible candidates, in specified order"
        return self.select("withdrawn", order, reverse)

    def hopeful(self, order="none", reverse=False):
        "select and return list of hopeful candidates, in specified order"
        return self.select("hopeful", order, reverse)

    def elected(self, order="none", reverse=False):
        "select and return list of withdrawn candidates, in specified order"
        return self.select("elected", order, reverse)

    def defeated(self, order="none", reverse=False):
        "select and return list of defeated candidates, in specified order"
        return self.select("defeated", order, reverse)

    def notpending(self, order="none", reverse=False):
        "select and return list of elected and not pending candidates, in specified order"
        return self.select("notpending", order, reverse)

    def pending(self, order="none", reverse=False):
        "select and return list of elected candidates pending transfer, in specified order"
        return self.select("pending", order, reverse)


class Candidate(object):
    '''
    a candidate, with state
    '''
    def __init__(self, E, cid, ballotOrder, tieOrder, cname, cnick, isWithdrawn):
        "new candidate"
        # immutable properties
        self.E = E
        self.cid = cid              # candidate id
        self.order = ballotOrder    # ballot order
        self.tieOrder = tieOrder    # tie-breaking order
        self.name = cname           # candidate name
        self.nick = str(cid) if cnick is None else str(cnick)
        # mutable properties
        self.state = "withdrawn" if isWithdrawn else "hopeful"  # withdrawn, hopeful, elected, etc
        if E is None:
            self.vote = None        # in support of unit tests
        else:
            self.vote = E.V0        # current vote total
        self.kf = None              # current keep factor (meek)
        self.quotient = None        # current quotient (qpq)
        self.pending = False        # surplus-transfer pending (wigm)

    @property
    def surplus(self):
        "return candidate's current surplus vote"
        s = self.vote - self.E.quota
        return self.E.V0 if s < self.E.V0 else s
        
    def elect(self, msg='Elect'):
        '''
        Meek, QPQ: elect a candidate
        WIGM: move a candidate from pending to elected on surplus transfer
        '''
        self.state = "elected"
        self.pending = False
        self.E.logAction('elect', "%s: %s" % (msg, self.name))

    def pend(self, msg='Elect, transfer pending'):
        '''
        WIGM: set a candidate elected pending transfer
        '''
        self.state = "elected"
        self.pending = True
        self.E.logAction('pend', "%s: %s" % (msg, self.name))

    def unelect(self):
        "QPQ: unelect a candidate (qpq restart)"
        self.state = "hopeful"

    def defeat(self, msg='Defeat'):
        "defeat a candidate"
        self.state = "defeated"
        self.E.logAction('defeat', "%s: %s" % (msg, self.name))

    def code(self):
        "return a one-letter state code for a candidate"
        if self.state == "withdrawn": return 'W'
        if self.state == "hopeful": return 'H'
        if self.state == "elected":
            if self.E.rule.method == 'wigm' and self.pending: return 'e'
            return 'E'
        if self.state == "defeated": return 'D'
        return '?'  # pragma: no cover

    def __str__(self):
        "use candidate name as the string representation"
        return self.name

    def __hash__(self):
        "use candidate id as the candidate hash"
        return self.cid

    def __eq__(self, other):
        "test for equality of cid"
        if isinstance(other, int):
            return self.cid == other
        if isinstance(other, str):
            return str(self.cid) == other
        if other is None:
            return False
        return self.cid == other.cid
