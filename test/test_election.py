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
from droop.election import Candidate, CandidateSet

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

class CandidateSetTest(unittest.TestCase):
    "test class CandidateSet"
    
    def testCSinit(self):
        "create a CandidateSet and check it out"
        cset = CandidateSet(set((1,2,3)))
        self.assertTrue(len(cset) == 3, 'set with three members')
        self.assertTrue(isinstance(cset, set))
        self.assertTrue(isinstance(cset, CandidateSet))

    def testCSunion(self):
        "test CandidateSet union method"
        cset1 = CandidateSet(set((1,2,3)))
        cset2 = CandidateSet(set((2,3,4)))
        cset = cset1 | cset2
        self.assertTrue(len(cset) == 4, 'union set has four members')
        self.assertTrue(isinstance(cset, set))
        self.assertTrue(isinstance(cset, CandidateSet))

    def testCSintersection(self):
        "test CandidateSet intersection method"
        cset1 = CandidateSet(set((1,2,3)))
        cset2 = CandidateSet(set((2,3,4)))
        cset = cset1 & cset2
        self.assertTrue(len(cset) == 2, 'union set has two members')
        self.assertTrue(isinstance(cset, set))
        self.assertTrue(isinstance(cset, CandidateSet))

    def testCSdifference(self):
        "test CandidateSet difference method"
        cset1 = CandidateSet(set((1,2,3)))
        cset2 = CandidateSet(set((2,3,4)))
        cset = cset1 - cset2
        self.assertEqual(len(cset), 1, 'difference set has one member')
        self.assertTrue(isinstance(cset, set))
        self.assertTrue(isinstance(cset, CandidateSet))

    def testCSadd(self):
        "test add to set"
        cset = CandidateSet(set((1,2,3)))
        cset.add(4)
        self.assertEqual(len(cset), 4, 'result set has four members')
        self.assertTrue(isinstance(cset, set))
        self.assertTrue(isinstance(cset, CandidateSet))

if __name__ == '__main__':
    unittest.main()