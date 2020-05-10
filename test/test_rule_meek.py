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
from __future__ import absolute_import
import unittest
from droop import electionRuleNames
from droop.election import Election
from droop.profile import ElectionProfile
from droop.common import UsageError
from .common import testdir, doDumpCompare

class ElectionNameTest(unittest.TestCase):
    "make sure we're in the book"

    def testElectionNames(self):
        "meek & warren are valid names"
        self.assertTrue('meek' in electionRuleNames())
        self.assertTrue('warren' in electionRuleNames())

    def testMeekWarren1(self):
        "meek responds to warren"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        profile = ElectionProfile(data=b)
        E = Election(profile, dict(rule='warren'))
        self.assertEqual(E.rule.tag(), 'warren-o9')
        self.assertRaises(UsageError, Election, profile, dict(rule='warren', defeat_batch='whatever'))

class ElectionCountTest(unittest.TestCase):
    "test some counts"

    @staticmethod
    def doCount(options, blt):
        "run the count and return the Election"
        p = ElectionProfile(testdir + '/blt/' + blt)
        E = Election(p, options)
        E.count()
        return E

    def testElectionCount1(self):
        "try meek default"
        E = self.doCount(dict(rule='meek'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount2(self):
        "try meek default"
        E = self.doCount(dict(rule='meek', defeat_batch='none'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount7(self):
        "meek stable state"
        E = self.doCount(dict(rule='meek', precision=7, omega=7), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testNickReport(self):
        "using nicknames shouldn't alter dump or report"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 [nick a b c] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b1), dict(rule='meek'))
        E.count()
        r1 = E.report()
        d1 = E.dump()
        E = Election(ElectionProfile(data=b2), dict(rule='meek'))
        E.count()
        r2 = E.report()
        d2 = E.dump()
        self.assertEqual(r1, r2)
        self.assertEqual(d1, d2)

    def testAllEqual(self):
        "profile with only equal preferences"
        b = '''3 2 1 1=2 0 1 2=3 0 1 1=3 0 0 "A" "B" "C" "three-way tie"'''
        E = Election(ElectionProfile(data=b), dict(rule='meek'))
        E.count()
        self.assertEqual(len(E.elected), E.nSeats)

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    @staticmethod
    def getDump(options, base):
        "run a count and return the dump"
        blt = '%s/blt/%s.blt' % (testdir, base)
        E = Election(ElectionProfile(blt), options)
        E.count()
        return E.dump()

    def testElectionDumpRationalMeek(self):
        "try several counts & dumps with rational arithmetic"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        rulename = 'meek'
        for blt in blts:
            self.assertTrue(doDumpCompare(dict(rule=rulename, arithmetic='rational'), blt),
                            '%s %s.blt' % (rulename, blt))

    def testElectionDumpRationalWarren(self):
        "try several counts & dumps with rational arithmetic"
        blts = ('42', '42t', '513', 'SC')  # SC-Vm-12 runs too long with warren+rational
        rulename = 'warren'
        for blt in blts:
            self.assertTrue(doDumpCompare(dict(rule=rulename, arithmetic='rational'), blt),
                            '%s %s.blt' % (rulename, blt))

    def testElectionDumpFixedVsGuardedMeek(self):
        "meek: guarded with guard=0 should match fixed"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        rulename = 'meek'
        for blt in blts:
            fdump = self.getDump(dict(rule=rulename, arithmetic='fixed', precision=6, omega=3), blt)
            gdump = self.getDump(dict(rule=rulename, arithmetic='guarded', precision=6, guard=0, omega=3), blt)
            self.assertEqual(fdump, gdump, 'guarded with guard=0 should match fixed')

    def testStableState(self):
        "meek: generate a stable state"
        fdump = self.getDump(dict(rule='meek', arithmetic='fixed', precision=6, omega=4), 'SC-Vm-12')
        gdump = self.getDump(dict(rule='meek', arithmetic='guarded', precision=6, guard=0, omega=4), 'SC-Vm-12')
        self.assertEqual(fdump, gdump, 'guarded with guard=0 should match fixed (stable state)')
        self.assertTrue(fdump.find('stable') > 0, 'should be stable state')

    def testElectionDumpRationalVsGuardedMeek(self):
        "meek: guarded should match rational"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        rulename = 'meek'
        for blt in blts:
            fdump = self.getDump(dict(rule=rulename, arithmetic='rational', omega=9, display=18), blt)
            gdump = self.getDump(dict(rule=rulename, arithmetic='guarded', precision=18, guard=9, omega=9), blt)
            self.assertEqual(fdump, gdump, 'guarded should match rational')

if __name__ == '__main__':
    unittest.main()
