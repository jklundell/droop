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
import sys, os
testdir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.normpath(os.path.join(testdir, '..'))
if basedir not in sys.path: sys.path.insert(0, os.path.normpath(basedir))

from droop.election import Election
from droop import electionRuleNames, electionRule
from droop.profile import ElectionProfile, ElectionProfileError
from droop import rules as R

#from droop.rules.mpls import Rule as Mpls

class ElectionInitTest(unittest.TestCase):
    "test election.__init__"
    
    Profile = None   # profile
    Rule = None      # rule
    
    def setUp(self):
        "initialize profile and rule"
        path = testdir + '/blt/42.blt'
        self.Profile = ElectionProfile(path)
        self.Rule = R.mpls.Rule

    def testElectionInit(self):
        "check that election is initialized"
        options = dict()
        E = Election(self.Rule, self.Profile, options)
        self.assertTrue(E.rule == self.Rule, 'bad rule class')
        self.assertEqual(len(options), 2, 'mpls should set two options')
        self.assertEqual(options['arithmetic'], 'fixed', 'mpls should set arithmetic=fixed')
        self.assertEqual(options['precision'], 4, 'mpls should set precision=4')

    def testElectionCount1(self):
        "try a basic count"
        options = dict()
        E = Election(self.Rule, self.Profile, options)
        E.count()
        self.assertEqual(len(E.elected), E.nSeats)

class ElectionCountTest(unittest.TestCase):
    "test some counts"

    def doCount(self, Rule, options, blt):
        "run the count and return the Election"
        p = ElectionProfile(testdir + '/blt/' + blt)
        E = Election(Rule, p, options)
        E.count()
        return E

    def testElectionCount1(self):
        "try a basic count"
        options = dict()
        E = self.doCount(R.mpls.Rule, options, '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount2(self):
        "try a bigger count"
        options = dict()
        E = self.doCount(R.mpls.Rule, options, 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount3(self):
        "try wigm default"
        options = dict()
        E = self.doCount(R.wigm.Rule, options, '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount4(self):
        "try meek default"
        options = dict()
        E = self.doCount(R.meek.Rule, options, '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount5(self):
        "try meek_prf default"
        options = dict()
        E = self.doCount(R.meek_prf.Rule, options, '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)


if __name__ == '__main__':
    unittest.main()