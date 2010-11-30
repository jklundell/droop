#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' 
Unit test for droop.election package

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
import unittest

import common  # to set sys.path
from droop.election import Candidate, Candidates

if common.pyflakes: # satisfy pyflakes that we're using common
    pass

class CandidateTest(unittest.TestCase):
    "test class Candidate"
    
    def testCandidateString(self):
        "candidate string is its cname"
        c1 = Candidate(None, 1, 2, 2, 'abc', None, False)  # Election, cid, ballotOrder, tieOrder, cname, cnick, isWithdrawn
        self.assertEqual(str(c1), 'abc', 'candidate string is its cname')

    def testCandidateHash(self):
        "candidate hash is its ID"
        c1 = Candidate(None, 1, 2, 2, 'abc', None, False)
        self.assertEqual(hash(c1), 1, 'candidate hash is its ID')

    def testCandidateCompare(self):
        "compare candidates by ID"
        c1 = Candidate(None, 1, 2, 2, 'abc', None, False)
        c2 = Candidate(None, 1, 3, 3, 'def', None, False)
        self.assertEqual(c1, c2, 'candidates are compared by ID')

class CandidatesTest(unittest.TestCase):
    "test class Candidates"

    def testCandidates(self):
        "general test of Candidates API"
        C = Candidates()
        c1 = Candidate(None, 1, 1, 3, 'Able', None, False)      # Election, cid, ballotOrder, tieOrder, cname, cnick, isWithdrawn
        c2 = Candidate(None, 2, 2, 2, 'Baker', None, False)
        c3 = Candidate(None, 3, 3, 1, 'Charlie', None, False)
        c1.vote = 1
        c2.vote = 3
        c3.vote = 2
        C.add(c1)
        C.add(c2)
        C.add(c3)
        c2.state = 'elected'
        c3.state = 'elected'
        c3.pending = True
        C2 = C.copy()
        self.assertEqual(C, C2, "copy Candidates")
        self.assertEqual(C.byTieOrder([c1, c2, c3]), [c3, c2, c1], "tie order")
        self.assertEqual(C.byTieOrder([c1, c2, c3], reverse=True), [c1, c2, c3], "reverse tie order")
        self.assertEqual(C.byBallotOrder([c1, c2, c3]), [c1, c2, c3], "ballot order")
        self.assertEqual(C.byBallotOrder([c1, c2, c3], reverse=True), [c3, c2, c1], "reverse ballot order")
        self.assertEqual(C.byVote([c1, c2, c3]), [c1, c3, c2], "vote order")
        self.assertEqual(C.select('all', 'ballot'), [c1, c2, c3], "all candidates, ballot order")
        self.assertEqual(C.select('eligible', 'ballot', reverse=True), [c3, c2, c1], "eligible candidates, reverse ballot order")
        self.assertEqual(C.select('eligible', 'tie'), [c3, c2, c1], "eligible candidates, tie order")
        self.assertEqual(C.select('elected', 'ballot'), [c2, c3], "elected candidates, ballot order")
        self.assertEqual(C.notpending(), [c2], "elected-not-pending candidate")
        self.assertRaises(ValueError, C.select, 'all', "bad-order")

if __name__ == '__main__':
    unittest.main()
