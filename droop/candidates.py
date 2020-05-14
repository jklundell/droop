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


import copy

class Candidates(set):
    '''
    all candidates
    '''
    def __init__(self, E=None):
        "new Candidates"
        super(Candidates, self).__init__()
        self.E = E              # Election
        self._byCid = dict()    # side table: cid -> Candidate

    def copy(self):
        "return a copy of ourself"
        C = Candidates(self.E)
        for c in self:
            super(Candidates, C).add(copy.copy(c))
        return C

    def add(self, c):
        "add a candidate"
        self._byCid[c.cid] = c  # side table for lookup by candidate ID
        super(Candidates, self).add(c)
        if self.E is not None:  # accommodate unit test
            if c.state == 'withdrawn':
                self.E.log("Add withdrawn: %s" % c.name)
            elif c.isUndeclared:
                self.E.log("Add undeclared: %s" % c.name)
            else:
                self.E.log("Add eligible: %s" % c.name)

    def byCid(self, cid):
        "look up a candidate by candidate ID"
        return self._byCid[cid]

    def cidList(self, state='all'):
        '''
        return a list of CIDs, in ballot order

        used for reporting
        '''
        return [c.cid for c in self.select(state, order='ballot')]

    def cDict(self):
        '''
        return dict of candidate static info, keyed by CID
        variant state is not included (see cState())

        used for reporting
        '''
        cdict = dict()
        for c in self.select('all'):
            cdict[c.cid] = c.as_dict(ro=True)
        return cdict

    def cState(self):
        '''
        return a dict of candidate state, keyed by CID
        invariant state is not included (see cDict())
        withdrawn candidates have an abbreviated state (see c.as_dict())

        used for reporting
        '''
        cstate = dict()
        for c in self.select('all'):
            cstate[c.cid] = c.as_dict(rw=True)
        return cstate

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

    def select(self, state, order='none', reverse=False):
        "select and return list of candidates with specified state, optionally in specified order"
        if state == 'all':
            candidates = self   # set of all
        elif state == 'eligible':
            candidates = [c for c in self if c.state != 'withdrawn']
        elif state == 'pending':
            candidates = [c for c in self if c.state == 'elected' and c.pending]
        elif state == 'notpending':
            candidates = [c for c in self if c.state == 'elected' and not c.pending]
        else:
            candidates = [c for c in self if c.state == state]  # list of all
        if order == 'none':
            return candidates
        if order == 'ballot':
            return self.byBallotOrder(candidates, reverse=reverse)
        if order == 'tie':
            return self.byTieOrder(candidates, reverse=reverse)
        if order == 'vote':
            return self.byVote(candidates, reverse=reverse)
        raise ValueError('unknown candidate sort order: %s' % order)

    def eligible(self, order='none', reverse=False):
        "select and return list of eligible candidates, in specified order"
        return self.select('eligible', order, reverse)

    def withdrawn(self, order='none', reverse=False):
        "select and return list of eligible candidates, in specified order"
        return self.select('withdrawn', order, reverse)

    def hopeful(self, order='none', reverse=False):
        "select and return list of hopeful candidates, in specified order"
        return self.select('hopeful', order, reverse)

    def elected(self, order='none', reverse=False):
        "select and return list of withdrawn candidates, in specified order"
        return self.select('elected', order, reverse)

    def defeated(self, order='none', reverse=False):
        "select and return list of defeated candidates, in specified order"
        return self.select('defeated', order, reverse)

    def notpending(self, order='none', reverse=False):
        "select and return list of elected and not pending candidates, in specified order"
        return self.select('notpending', order, reverse)

    def pending(self, order='none', reverse=False):
        "select and return list of elected candidates pending transfer, in specified order"
        return self.select('pending', order, reverse)
