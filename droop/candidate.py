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

class Candidate(object):
    '''
    a candidate, with state
    '''
    def __init__(self, E, cid, ballotOrder, tieOrder, cname, cnick, isWithdrawn, isUndeclared):
        "new candidate"
        # immutable properties
        self.E = E
        self.cid = cid              # candidate id
        self.order = ballotOrder    # ballot order
        self.tieOrder = tieOrder    # tie-breaking order
        self.name = cname           # candidate name
        self.nick = str(cid) if cnick is None else str(cnick)
        # mutable properties
        self.state = 'withdrawn' if isWithdrawn else 'hopeful'  # withdrawn, hopeful, elected, etc
        self.isUndeclared = isUndeclared
        if E is None:
            self.vote = None        # in support of unit tests
        else:
            self.vote = E.V0        # current vote total
        self.kf = None              # current keep factor (meek)
        self.quotient = None        # current quotient (qpq)
        self.pending = None         # surplus-transfer pending (wigm)

    def as_dict(self, ro=False, rw=False):
        "return as a dict suitable for JSON encoding"
        cdict = dict()
        if ro:
            cdict['cid'] = self.cid
            cdict['ballot_order'] = self.order
            cdict['tie_order'] = self.tieOrder
            cdict['name'] = self.name
            cdict['nick'] = self.nick
        if rw:
            cdict['state'] = self.state
            cdict['code'] = self.code()
            if self.state != 'withdrawn':
                cdict['vote'] = self.vote
                if self.kf is not None:
                    cdict['kf'] = self.kf
                if self.quotient is not None:
                    cdict['quotient'] = self.quotient
                if self.pending is not None:
                    cdict['pending'] = self.pending
        return cdict

    @property
    def surplus(self):
        "return candidate's current surplus vote"
        s = self.vote - self.E.quota
        return self.E.V0 if s < self.E.V0 else s

    def elect(self, msg=None, pending=False):
        '''
        Meek, QPQ: elect a candidate
        WIGM: elect a candidate, optionally pending surplus transfer
        '''
        self.state = 'elected'
        if msg is None:
            msg = 'Elect, transfer pending' if pending else 'Elect'
        self.pending = pending
        self.E.logAction('elect', "%s: %s" % (msg, self.name))

    def unpend(self, msg=None):
        '''
        WIGM: clear the transfer-pending flag
        '''
        assert self.state == 'elected'
        assert self.pending
        self.pending = False
        if msg:
            self.E.logAction('unpend', "%s: %s" % (msg, self.name))

    def unelect(self):
        "QPQ: unelect a candidate (qpq restart)"
        self.state = 'hopeful'

    def defeat(self, msg='Defeat'):
        "defeat a candidate"
        self.state = 'defeated'
        self.E.logAction('defeat', "%s: %s" % (msg, self.name))

    def code(self):
        "return a one-letter state code for a candidate"
        if self.state == 'withdrawn':
            return 'W'
        if self.state == 'hopeful':
            return 'H'
        if self.state == 'elected':
            if self.E.rule.method == 'wigm' and self.pending:
                return 'e'
            return 'E'
        if self.state == 'defeated':
            return 'D'
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
