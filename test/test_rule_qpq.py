#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' 
Unit test for droop.rules package

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
import os

from common import testdir, doDumpCompare
from droop import electionRuleNames, electionRule
from droop.election import Election
from droop.profile import ElectionProfile

from droop.rules.qpq import Rule

class TestBasic(unittest.TestCase):
    "test rules.__init__"
    
    def testRuleName(self):
        "check the list of names for qpq"
        self.assertTrue('qpq' in electionRuleNames(), 'one of the rule names is qpq')

    def testElectionRule(self):
        "look up one election rule"
        self.assertEqual(electionRule('qpq'), Rule, 'the qpq Rule should match its name lookup')

    def testQpq(self):
        "qpq is is a qpq variant"
        self.assertEqual(Rule.method, 'qpq')

class TestQpq(unittest.TestCase):
    '''
    Create an Election instance from a simple profile 
    and the QPQ rule and test its basic initialization,
    and that it elects the specified number of seats.
    '''
    
    def setUp(self):
        "initialize profile and rule"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.Profile = ElectionProfile(data=b)
        self.options = dict(rule='qpq')
        self.E = Election(self.Profile, self.options)

    def testElectionInit(self):
        "check that election is initialized"
        self.assertTrue(self.E.rule.__class__.__name__ == 'Rule', 'bad rule class')
        self.assertEqual(len(self.options), 5, 'qpq should set five options')
        self.assertEqual(self.options['arithmetic'], 'guarded', 'qpq should set arithmetic=guarded')
        self.assertEqual(self.options['precision'], 9, 'qpq should set precision=9')
        self.assertEqual(self.options['guard'], None, 'qpq should set guard=None')
        self.assertEqual(self.options['display'], None, 'qpq should set display=None')
        self.assertEqual(self.E.candidates[1].name, "Castor")
        self.assertEqual(str(self.E.candidates[1]), "Castor")
        self.assertTrue(self.E.candidates[1] == 1)
        self.assertTrue(self.E.candidates[1] == '1')
        self.assertFalse(self.E.candidates[1] == None)

    def testElectionTieOrder(self):
        "test default tie order"
        for c in self.E.candidates.values():
            self.assertEqual(c.order, c.tieOrder)

    def testElectionCount1(self):
        "try a basic count"
        self.E.count()
        self.assertEqual(len(self.E.elected), self.E.nSeats)

class ElectionCountTest(unittest.TestCase):
    "test some counts"

    def doCount(self, options, blt):
        "run the count and return the Election"
        p = ElectionProfile(testdir + '/blt/' + blt)
        E = Election(p, options)
        E.count()
        return E

    def testElectionCount1(self):
        "try a basic count"
        E = self.doCount(dict(rule='qpq'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionTieCount(self):
        "check a different tiebreaking order"
        E = self.doCount(dict(rule='qpq'), '42t.blt')
        tieOrder = [0, 3, 2, 1]
        for c in E.candidates.values():
            self.assertEqual(c.tieOrder, tieOrder[c.order])

    def testElectionCount2(self):
        "try a bigger election"
        E = self.doCount(dict(rule='qpq'), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionQpq1(self):
        "qpq: everyone elected at first"
        b = '''3 2 4 1 2 0 4 2 1 0 1 3 0 0 "a" "b" "c" "2 elected at first"'''
        E = Election(ElectionProfile(data=b), dict(rule='qpq'))
        E.count()
        self.assertEqual(len(E.elected), 2)

    def testNickReport(self):
        "using nicknames shouldn't alter dump or report"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 [nick a b c] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b1), dict(rule='qpq'))
        E.count()
        r1 = E.report()
        d1 = E.dump()
        E = Election(ElectionProfile(data=b2), dict(rule='qpq'))
        E.count()
        r2 = E.report()
        d2 = E.dump()
        self.assertEqual(r1, r2)
        self.assertEqual(d1, d2)

class ElectionRefTest(unittest.TestCase):
    "test known results of reference elections"
    
    def doQpqCount(self, file):
        "each of five elections from the Woodall paper"
        blt = os.path.join(testdir, 'blt', 'qpq', file)
        E = Election(ElectionProfile(blt), dict(rule='qpq'))
        E.count()
        return E
        
    def testQpq1(self):
        "test qpq1"
        E = self.doQpqCount('qpq1.blt')
        self.assertEqual(len(E.elected), 3)
        elected = [c.name for c in E.elected]
        self.assertEqual(elected, ['a', 'b', 'c'])

    def testQpq2(self):
        "test qpq2"
        E = self.doQpqCount('qpq2.blt')
        self.assertEqual(len(E.elected), 3)
        elected = [c.name for c in E.elected]
        self.assertEqual(elected, ['a', 'b', 'c'])

    def testQpq3(self):
        "test qpq3"
        E = self.doQpqCount('qpq3.blt')
        self.assertEqual(len(E.elected), 5)
        elected = [c.name for c in E.elected]
        self.assertEqual(elected, ['a', 'b', 'c', 'd', 'e'])

    def testQpq4(self):
        "test qpq4"
        E = self.doQpqCount('qpq4.blt')
        self.assertEqual(len(E.elected), 5)
        elected = [c.name for c in E.elected]
        self.assertEqual(elected, ['a', 'b', 'd', 'e', 'f'])

    def testQpq5(self):
        "test qpq5"
        E = self.doQpqCount('qpq5.blt')
        self.assertEqual(len(E.elected), 3)
        elected = [c.name for c in E.elected]
        self.assertEqual(elected, ['a', 'c', 'e'])

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    def testElectionDump(self):
        "try a basic count & dump"
        self.assertTrue(doDumpCompare(dict(rule='qpq'), '42'), 'QPQ 42.blt')

    def testElectionDumpu(self):
        "try a basic count & dump with utf-8 blt"
        self.assertTrue(doDumpCompare(dict(rule='qpq'), '42u'), 'QPQ 42u.blt')

if __name__ == '__main__':
    unittest.main()