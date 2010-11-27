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

from common import testdir
from droop.election import Election
from droop.profile import ElectionProfile
from droop import electionRuleNames

class RuleBasicTest(unittest.TestCase):
    "make sure we're in the book"
    
    def testElectionNames(self):
        self.assertTrue('wigm-prf' in electionRuleNames())

    def testArithmetic(self):
        "wigm-prf uses fixed"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b), dict(rule='wigm-prf', arithmetic='guarded', abc=4))
        self.assertEqual(E.options.getopt('arithmetic'), 'fixed')
        self.assertEqual(E.options.getopt('precision'), 4)
        self.assertEqual(E.options.overrides(), ['arithmetic'])
        self.assertEqual(E.options.unused(), ['abc'])

    def testDefeatBatch(self):
        "tag is name of rule"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b), dict(rule='wigm-prf'))
        self.assertEqual(E.rule.tag(), 'wigm-prf')
        E = Election(ElectionProfile(data=b), dict(rule='wigm-prf-batch'))
        self.assertEqual(E.rule.tag(), 'wigm-prf-batch')


class ElectionCountTest(unittest.TestCase):
    "test some counts"

    def doCount(self, options, blt):
        "run the count and return the Election"
        p = ElectionProfile(testdir + '/blt/' + blt)
        E = Election(p, options)
        E.count()
        return E

    def testElectionCount1(self):
        "try wigm-prf variants"
        for variant in ('wigm-prf', 'wigm-prf-batch'):
            E = self.doCount(dict(rule=variant), '42.blt')
            self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount2(self):
        "try wigm-prf with integer quota"
        E = self.doCount(dict(rule='wigm-prf', integer_quota='true'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount3(self):
        "try wigm-prf with alternative precision; should stick at default precision"
        E = self.doCount(dict(rule='wigm-prf', precision='8'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)
        self.assertEqual(E.V.precision, 4)

    def testDefeatRemaining(self):
        "count a profile that has hopeful candidates left over to defeat"
        b = '''3 2  4 1 0  4 2 0  2 3 0  0 "Castor" "Pollux" "Helen" "test defeat-remaining"'''
        E = Election(ElectionProfile(data=b), dict(rule='wigm-prf'))
        E.count()
        elected = [c.name for c in E.elected]
        self.assertEqual(elected, ['Castor', 'Pollux'])
        defeated = [c.name for c in E.defeated]
        self.assertEqual(defeated, ['Helen'])
        report = E.report()
        self.assertTrue(report.find('Defeat remaining'))

    def testNickReport(self):
        "using nicknames shouldn't alter dump or report"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 [nick a b c] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b1), dict(rule='wigm-prf'))
        E.count()
        r1 = E.report()
        d1 = E.dump()
        E = Election(ElectionProfile(data=b2), dict(rule='wigm-prf'))
        E.count()
        r2 = E.report()
        d2 = E.dump()
        self.assertEqual(r1, r2)
        self.assertEqual(d1, d2)

if __name__ == '__main__':
    unittest.main()
