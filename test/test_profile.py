''' 
Unit test for droop.profile module

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

from droop.profile import ElectionProfile
from droop.profile import ElectionProfileError

p_42 = '''3 2
4 1 2 0
2 3 0
0
"Castor"
"Pollux"
"Helen"
"Pollux and Helen should tie"
'''

p_42a = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
p_42b = '''3 2 4 1 2 0 2 3 0 0 /* comment */ "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
p_42c = '''3 2 4 1 2 0 2 3 0 0 /* nested /*comment */ */ "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
p_42d = '''3 2 4 1 2 0 2 3 0 0 /* nested /*comment*/ */ "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''

p_42_bad1 = '''x 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
p_42_bad2 = '''3 2 4 1 2 0 2 3 0 0 Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
p_42_bad3 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie '''

p_42bads = '''1 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
p_42badb = '''3 2 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
p_42badc = '''3 2 4 1 2 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''

p_42w = '''4 2 -4 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Bob" "Pollux and Helen should tie"'''


class ProfileTest(unittest.TestCase):
    "test profile-class initialization"
    
    def testNoData(self):
        "exception if no profile data supplied"
        self.assertRaises(ElectionProfileError, ElectionProfile)

    def testInitSeats(self):
        "normal init: 2 seats"
        self.assertEqual(ElectionProfile(data=p_42).nSeats, 2)

    def testBadNSeats(self):
        "exception if too few seats"
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42bads)

    def testBadNBallots(self):
        "exception if too few ballots"
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42badb)

    def testDupeCand(self):
        "exception candidate duplicated"
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42badc)

    def testInitOneLine(self):
        "normal init: 2 seats (no newlines)"
        self.assertEqual(ElectionProfile(data=p_42a).nSeats, 2)

    def testInitComment(self):
        "normal init: 2 seats (comment)"
        self.assertEqual(ElectionProfile(data=p_42b).nSeats, 2)

    def testInitNestedComment(self):
        "normal init: 2 seats (nested comment)"
        self.assertEqual(ElectionProfile(data=p_42c).nSeats, 2)

    def testInitOneTokenComment(self):
        "normal init: 2 seats (single-token comment)"
        self.assertEqual(ElectionProfile(data=p_42d).nSeats, 2)

    def testInitTitle(self):
        "normal init: title set"
        self.assertEqual(ElectionProfile(data=p_42).title, '"Pollux and Helen should tie"')

    def testInitnBallots(self):
        "normal init: 6 ballots"
        self.assertEqual(ElectionProfile(data=p_42).nBallots, 6)

    def testInitnBallotLines(self):
        "normal init: 2 ballot lines"
        self.assertEqual(len(ElectionProfile(data=p_42).ballotLines), 2)

    def testInitNoWithdrawn(self):
        "normal init: 0 withdrawn"
        self.assertEqual(len(ElectionProfile(data=p_42a).withdrawn), 0)

    def testInitOneWithdrawn(self):
        "normal init: 1 withdrawn"
        self.assertEqual(len(ElectionProfile(data=p_42w).withdrawn), 1)

    def testInitOneWithdrawnEligible(self):
        "normal init: 1 withdrawn"
        self.assertEqual(len(ElectionProfile(data=p_42w).eligible), 3)

    def testInitBobName(self):
        "normal init: name of candidate"
        self.assertEqual(ElectionProfile(data=p_42w)._candidateName['4'], 'Bob')

    def testInitBobOrder(self):
        "normal init: order of candidate"
        self.assertEqual(ElectionProfile(data=p_42w)._candidateOrder['4'], 4)

    def testBadNcand(self):
        "exception bad candidate format"
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42_bad1)

    def testBadName(self):
        "exception bad candidate name"
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42_bad2)

    def testBadTitle(self):
        "exception bad title"
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42_bad3)

    def testCandidateName(self):
        "fetch a candidate name"
        p = ElectionProfile(data=p_42a)
        self.assertEqual(p.candidateName('1'), 'Castor')

    def testCandidateOrder(self):
        "fetch a candidate order"
        p = ElectionProfile(data=p_42a)
        self.assertEqual(p.candidateOrder('1'), 1)

    def testBadFile(self):
        "exception bad file name"
        self.assertRaises(ElectionProfileError, ElectionProfile, path='nofileatall')



if __name__ == '__main__':
    unittest.main()