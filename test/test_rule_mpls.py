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
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))

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

if __name__ == '__main__':
    unittest.main()