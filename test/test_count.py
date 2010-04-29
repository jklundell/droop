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
import os

from common import testdir, doDumpCompare
import droop
from droop.election import Election
from droop.profile import ElectionProfile
from droop import electionRuleNames

class ElectionBasics(unittest.TestCase):
    '''
    test Election.__init__
    
    Create an Election instance from a simple profile 
    and the Minneapolis rule and test its basic initialization,
    and that it elects the specified number of seats.
    '''

    def testRules(self):
        "basic test of each rule"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''

        for rulename in electionRuleNames():
            profile = ElectionProfile(data=b)
            options = dict(rule=rulename)
            E = Election(profile, options)
            self.assertTrue(E.rule.__name__ == 'Rule', 'bad rule class')
            self.assertTrue(len(options) >= 1, 'rule should set/leave at least one option')
            self.assertTrue(options.get('arithmetic', 'fixed') in ('fixed', 'integer', 'guarded', 'rational'), 'legal arithmetic')
            self.assertEqual(E.candidates[1].name, "Castor")
            self.assertEqual(str(E.candidates[1]), "Castor")
            self.assertTrue(E.candidates[1] == 1)
            self.assertTrue(E.candidates[1] == '1')
            self.assertFalse(E.candidates[1] == None)
            for c in E.candidates.values():
                self.assertEqual(c.order, c.tieOrder)
            E.count()
            self.assertEqual(len(E.elected), E.nSeats)

class ElectionHelps(unittest.TestCase):
    "check that helps dict is initialized"

    def testElectionHelps(self):
        "test helps"
        helps = Election.makehelp()
        self.assertTrue(isinstance(helps['rule'], str))
        self.assertTrue(isinstance(helps['arithmetic'], str))

class ElectionCountTest(unittest.TestCase):
    "test some counts"

    def doCount(self, options, blt):
        "run the count and return the Election"
        p = ElectionProfile(testdir + '/blt/' + blt)
        E = Election(p, options)
        E.count()
        return E

    def testElectionCount1(self):
        "try wigm default"
        E = self.doCount(dict(rule='wigm'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount2(self):
        "try wigm with integer quota"
        E = self.doCount(dict(rule='wigm', integer_quota='true'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount3(self):
        "try wigm with precision as string"
        E = self.doCount(dict(rule='wigm', precision='8'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)
        self.assertEqual(E.V.precision, 8)

    def testElectionCount4(self):
        "try meek default"
        E = self.doCount(dict(rule='meek'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount4a(self):
        "try meek default"
        E = self.doCount(dict(rule='meek', defeat_batch='none'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount5(self):
        "try prf-meek-basic default"
        E = self.doCount(dict(rule='prf-meek-basic'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount6(self):
        "prf-meek-basic stable state"
        E = self.doCount(dict(rule='prf-meek-basic', precision=7, omega=7), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount7(self):
        "meek-generic stable state"
        E = self.doCount(dict(rule='meek', precision=7, omega=7), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testNickReport(self):
        "using nicknames shouldn't alter dump or report"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 [nick a b c] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b1), dict(rule='scotland'))
        E.count()
        r1 = E.report()
        d1 = E.dump()
        E = Election(ElectionProfile(data=b2), dict(rule='scotland'))
        E.count()
        r2 = E.report()
        d2 = E.dump()
        self.assertEqual(r1, r2)
        self.assertEqual(d1, d2)

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    def getDump(self, options, base):
        "run a count and return the dump"
        blt = '%s/blt/%s.blt' % (testdir, base)
        E = Election(ElectionProfile(blt), options)
        E.count()
        return E.dump()

    def testElectionDumpWarren(self):
        "try a basic count & dump"
        self.assertTrue(doDumpCompare(dict(rule='warren'), '42'), 'Warren 42.blt')

    def testElectionDumpMPRFStable(self):
        "meek-prf-basic stable state"
        self.assertTrue(doDumpCompare(dict(rule='prf-meek-basic', precision=7, omega=7), 'SC-Vm-12'), 'meek-prf stable state')

    def testElectionDumps(self):
        "try several counts & dumps"
        blts = ('42', '42t', '42u', 'M135', '513', 'SC', 'SCw', 'SC-Vm-12')
        rulenames = droop.electionRuleNames()
        for blt in blts:
            for rulename in rulenames:
                Rule = droop.electionRule(rulename)
                self.assertTrue(doDumpCompare(dict(rule=rulename), blt), '%s %s.blt' % (Rule.info(), blt))

    def testElectionDumpRational(self):
        "try several counts & dumps with rational arithmetic"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        rulenames = ('meek', 'wigm')
        for blt in blts:
            for rulename in rulenames:
                Rule = droop.electionRule(rulename)
                self.assertTrue(doDumpCompare(dict(rule=rulename, arithmetic='rational'), blt), '%s %s.blt' % (Rule.info(), blt))

    def testElectionDumpFixedVsGuarded(self):
        "guarded with guard=0 should match fixed"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        rulenames = ('meek', 'wigm')
        for blt in blts:
            for rulename in rulenames:
                fdump = self.getDump(dict(rule=rulename, arithmetic='fixed', precision=6), blt)
                gdump = self.getDump(dict(rule=rulename, arithmetic='guarded', precision=6, guard=0), blt)
                self.assertEqual(fdump, gdump, 'guarded with guard=0 should match fixed')

    def testElectionDumpRationalVsGuarded(self):
        "guarded should match rational"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        rulenames = ('meek', 'wigm')
        for blt in blts:
            for rulename in rulenames:
                fdump = self.getDump(dict(rule=rulename, arithmetic='rational', omega=9, display=18), blt)
                gdump = self.getDump(dict(rule=rulename, arithmetic='guarded', precision=18, guard=9, omega=9), blt)
                self.assertEqual(fdump, gdump, 'guarded should match rational')

    def testElectionDumpRules(self):
        "run rule-specific counts"
        rulenames = droop.electionRuleNames()
        for rulename in rulenames:
            bltdir = os.path.join(testdir, 'blt', rulename)
            if os.path.isdir(bltdir):
                for blt in [blt for blt in os.listdir(bltdir) if blt.endswith('.blt')]:
                    self.assertTrue(doDumpCompare(dict(rule=rulename), blt, rulename), '%s/%s' % (rulename, blt))

if __name__ == '__main__':
    unittest.main()
