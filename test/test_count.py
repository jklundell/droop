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
import os

import droop
from droop.election import Election
from droop.profile import ElectionProfile
from droop.common import UsageError
from .common import testdir, doDumpCompare

class ElectionBasics(unittest.TestCase):
    '''
    test Election.__init__

    Create an Election instance from a simple profile
    and each rule and test its basic initialization,
    and that it elects the specified number of seats.
    '''

    def testRules(self):
        "basic test of each rule"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''

        profile = ElectionProfile(data=b)
        for rulename in droop.electionRuleNames():
            options = dict(rule=rulename)
            E = Election(profile, options)
            self.assertTrue(E.rule.__class__.__name__ == 'Rule', 'bad rule class')
            self.assertTrue(len(options) >= 1, 'rule should set/leave at least one option')
            self.assertTrue(E.options.getopt('arithmetic') in ('fixed', 'integer', 'guarded', 'rational'),
                            'legal arithmetic')
            candidates = E.C
            self.assertTrue("Castor" in [c.name for c in candidates])
            self.assertTrue("Castor" in [str(c) for c in candidates])
            self.assertTrue(1 in [c for c in candidates])
            for c in candidates:
                self.assertEqual(c.order, c.tieOrder)
            E.count()
            self.assertEqual(len(E.elected), E.nSeats)

    def testReports(self):
        "look at election outputs"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''

        profile = ElectionProfile(data=b)
        rulename = droop.electionRuleNames()[0]   # pick the first rule arbitrarily
        E = Election(profile, dict(rule=rulename))
        E.count()
        self.assertEqual(E.report().find('interrupted'), -1)
        self.assertTrue(E.report(intr=True).find('interrupted') > 0)
        E = Election(profile, dict(rule=rulename))
        E.count()
        self.assertEqual(E.dump().find('interrupted'), -1)
        self.assertTrue(E.dump(intr=True).find('interrupted') > 0)
        E = Election(profile, dict(rule=rulename))
        E.count()
        self.assertEqual(E.json().find('interrupted'), -1)
        self.assertTrue(E.json(intr=True).find('interrupted') > 0)
        r = E.record()
        self.assertTrue(r, dict)
        self.assertEqual(r['actions'][-1]['tag'], 'log')

class ElectionOptions(unittest.TestCase):
    "test options via [droop ...] in blt file"

    def testDroopOptions(self):
        "test [droop ...]"
        if 'meek' in droop.electionRuleNames():
            b = '''3 2 [droop arithmetic=fixed precision=4] 4 1 2 0 2 3 0 0
                "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
            E = Election(ElectionProfile(data=b), dict(rule='meek'))
            self.assertEqual(E.V.precision, 4)
            E = Election(ElectionProfile(data=b), dict(rule='meek', precision=6))
            self.assertEqual(E.V.precision, 6)
            b = '''3 2 [droop rational precision=4] 4 1 2 0 2 3 0 0
                "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
            E = Election(ElectionProfile(data=b), dict(rule='meek'))
            self.assertEqual(E.V.name, 'rational')
            b = '''3 2 [droop meek] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
            E = Election(ElectionProfile(data=b), dict())
            self.assertEqual(E.rule.method, 'meek')
            E = Election(ElectionProfile(data=b), None)
            self.assertEqual(E.rule.method, 'meek')
            b = '''3 2 [droop dump meek] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
            E = Election(ElectionProfile(data=b), None)
            self.assertTrue(E.options.getopt('dump'))
            b = '''3 2 [droop dump=true meek] 4 1 2 0 2 3 0 0
                "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
            E = Election(ElectionProfile(data=b), None)
            self.assertTrue(E.options.getopt('dump'))
            b = '''3 2 [droop dump=false meek] 4 1 2 0 2 3 0 0
                "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
            E = Election(ElectionProfile(data=b), None)
            self.assertFalse(E.options.getopt('dump'))
            # fake a path to test double-path logic
            b = '''3 2 [droop 42.blt 513.blt meek] 4 1 2 0 2 3 0 0
                "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
            self.assertRaises(UsageError, Election, ElectionProfile(data=b), dict())

class ElectionHelps(unittest.TestCase):
    "check that helps dict is initialized"

    def testElectionHelps(self):
        "test helps"
        helps = Election.makehelp()
        self.assertTrue(isinstance(helps['rule'], str))
        self.assertTrue(isinstance(helps['arithmetic'], str))

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    @staticmethod
    def getDump(options, base):
        "run a count and return the dump"
        blt = '%s/blt/%s.blt' % (testdir, base)
        E = Election(ElectionProfile(blt), options)
        E.count()
        return E.dump()

    def testElectionDumps(self):
        "try several counts & dumps"
        blts = ('42', '42t', '42u', 'M135', '513', 'SC', 'SCw', 'SC-Vm-12')
        rulenames = droop.electionRuleNames()
        for blt in blts:
            for rulename in rulenames:
                self.assertTrue(doDumpCompare(dict(rule=rulename), blt), '%s %s.blt' % (rulename, blt))

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
