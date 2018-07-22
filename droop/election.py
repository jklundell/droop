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

from __future__ import absolute_import
import sys
from .common import ElectionError
from .options import Options
from . import electionRule, electionRuleNames, ruleByName
from . import values, record
from .candidates import Candidates
from .candidate import Candidate

class Election(object):
    '''
    container for an election
    '''

    def __init__(self, electionProfile, options=None):
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

        if options is None:
            options = dict()
        if isinstance(options, dict):
            options = Options(options)
        options.update(options.parse(electionProfile.options), file_options=True)
        self.options = options
        rulename = options.getopt('rule')
        if rulename is None:
            raise ElectionError('no election rule specified')
        Rule = electionRule(rulename)    # get rule class
        if Rule is None:
            raise ElectionError('unknown election rule: %s' % rulename)
        self.rule = Rule(self)
        self.rule.options()     # allow rule to process options
        self.V = values.ArithmeticClass(self.options) # then set arithmetic
        self.V0 = self.V(0)  # constant zero for efficiency
        self.V1 = self.V(1)  # constant one for efficiency
        self.electionProfile = electionProfile
        self.erecord = record.ElectionRecord(self)
        self.round = 0  # counting-round number
        self.rounds = list()    # list of rounds for weak tiebreaking
        self.intr_logged = False

        self.quota = None
        self.surplus = None
        self.votes = None
        self.elected = None
        self.defeated = None
        self.withdrawn = None
        self.residual = None

        #  create candidate objects for candidates in election profile
        #
        self.C = Candidates(self)
        for cid in sorted(electionProfile.eligible | electionProfile.withdrawn):
            c = Candidate(self, cid, electionProfile.candidateOrder[cid],
                          electionProfile.tieOrder[cid],
                          electionProfile.candidateName[cid],
                          electionProfile.nickName[cid],
                          cid in electionProfile.withdrawn)
            self.C.add(c)

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
        for c in self.C:
            c.vote = self.V0
        ##
        self.rule.count()   ### count the election ###
        ##
        self.logAction('end', 'Count Complete')
        self.elected = self.C.elected()
        self.defeated = self.C.defeated()
        self.withdrawn = self.C.withdrawn()
        self.postCheck()    # post-election sanity check

    def postCheck(self):
        "post-election sanity check"
        nElected = len(self.elected)
        nEligible = len(self.C.eligible())
        assert(nElected == self.nSeats or
               nElected < self.nSeats and nElected == nEligible)

    def logAction(self, action, msg):
        "record an action"
        self.erecord.action(action, msg)

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
        helps['rule'] = 'available rules: %s' % ','.join(electionRuleNames())
        for name in electionRuleNames():
            ruleByName[name].helps(helps, name)
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
        return self.C.byCid(cid)

    @staticmethod
    def prog(msg):
        "log to the console (immediate output)"
        sys.stdout.write(msg)
        sys.stdout.flush()

    def seatsLeftToFill(self):
        "number of seats not yet filled"
        return self.nSeats - len(self.C.elected())

    def record(self):
        "return the election record as a dict"
        return dict(self.erecord)

    def report(self, intr=False):
        "return the election record as a formatted report"
        if intr and not self.intr_logged:
            self.log('** count interrupted; this round is incomplete **')
            self.intr_logged = True
        return self.erecord.report(intr)

    def dump(self, intr=False):
        "return the election record as tab-separated fields"
        if intr and not self.intr_logged:
            self.log('** count interrupted; this round is incomplete **')
            self.intr_logged = True
        return self.erecord.dump()

    def json(self, intr=False):
        "return the election record as a JSON string"
        if intr and not self.intr_logged:
            self.log('** count interrupted; this round is incomplete **')
            self.intr_logged = True
        return self.erecord.json()

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
            return self.E.C.byCid(self.ranking[self.index]) if self.index < len(self.ranking) else None

        @property
        def vote(self):
            "return total vote of this ballot"
            if self.multiplier == self.E.V1:
                return self.weight  # faster
            return self.weight * self.multiplier
