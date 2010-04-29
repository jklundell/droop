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

from common import testdir, doDumpCompare
from droop import electionRuleNames, electionRule
from droop.election import Election
from droop.profile import ElectionProfile

from droop.rules.mpls import Rule as Mpls

class MplsTestBasic(unittest.TestCase):
    "test rules.__init__"
    
    def testRuleNameMpls(self):
        "check the list of names for mpls"
        self.assertTrue('mpls' in electionRuleNames(), 'one of the rule names is mpls')

    def testElectionRule(self):
        "look up one election rule"
        self.assertEqual(electionRule('mpls'), Mpls, 'the mpls Rule should match its name lookup')

    def testMplsWigm(self):
        "mpls is is a wigm variant"
        self.assertEqual(Mpls.method(), 'wigm')

class MplsTest(unittest.TestCase):
    '''
    Create an Election instance from a simple profile 
    and the Minneapolis rule and test its basic initialization,
    and that it elects the specified number of seats.
    '''
    
    def setUp(self):
        "initialize profile and rule"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.Profile = ElectionProfile(data=b)
        self.options = dict(rule='mpls')
        self.E = Election(self.Profile, self.options)

    def testElectionInit(self):
        "check that election is initialized"
        self.assertTrue(self.E.rule == Mpls, 'bad rule class')
        self.assertEqual(len(self.options), 3, 'mpls should set three options')
        self.assertEqual(self.options['arithmetic'], 'fixed', 'mpls should set arithmetic=fixed')
        self.assertEqual(self.options['precision'], 4, 'mpls should set precision=4')
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
        E = self.doCount(dict(rule='mpls'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionTieCount(self):
        "check a different tiebreaking order"
        E = self.doCount(dict(rule='mpls'), '42t.blt')
        tieOrder = [0, 3, 2, 1]
        for c in E.candidates.values():
            self.assertEqual(c.tieOrder, tieOrder[c.order])

    def testElectionCount2(self):
        "try a bigger election"
        E = self.doCount(dict(rule='mpls'), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionMpls1(self):
        "mpls: everyone elected at first"
        p_mpls1 = '''3 2 4 1 2 0 4 2 1 0 1 3 0 0 "a" "b" "c" "2 elected at first"'''
        E = Election(ElectionProfile(data=p_mpls1), dict(rule='mpls'))
        E.count()
        self.assertEqual(len(E.elected), 2)

    def testNickReport(self):
        "using nicknames shouldn't alter dump or report"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 [nick a b c] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b1), dict(rule='mpls'))
        E.count()
        r1 = E.report()
        d1 = E.dump()
        E = Election(ElectionProfile(data=b2), dict(rule='mpls'))
        E.count()
        r2 = E.report()
        d2 = E.dump()
        self.assertEqual(r1, r2)
        self.assertEqual(d1, d2)

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    def testElectionDump(self):
        "try a basic count & dump"
        self.assertTrue(doDumpCompare(dict(rule='mpls'), '42'), 'Minneapolis 42.blt')

    def testElectionDumpu(self):
        "try a basic count & dump with utf-8 blt"
        self.assertTrue(doDumpCompare(dict(rule='mpls'), '42u'), 'Minneapolis 42u.blt')

if __name__ == '__main__':
    unittest.main()