#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from common import testdir
from droop.profile import ElectionProfile, ElectionProfileError

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
p_42u = '''3 2 4 1 2 0 2 3 0 0 "Cåstor" "Pøllux" "Hélen" "Pøllux and Hélen should tie"'''

class ProfileTest(unittest.TestCase):
    "test profile-class initialization"
    
    def testNoData(self):
        "exception if no profile data supplied"
        self.assertRaises(ElectionProfileError, ElectionProfile)

    def testEmptyData(self):
        "exception if empty profile data supplied"
        self.assertRaises(ElectionProfileError, ElectionProfile, data='')

    def testTruncData(self):
        "exception if truncated profile data supplied"
        self.assertRaises(ElectionProfileError, ElectionProfile, data='1 2')

    def testInitSeats(self):
        "normal init: 2 seats"
        self.assertEqual(ElectionProfile(data=p_42).nSeats, 2)

    def testTooFewSeats(self):
        "exception if too few seats"
        b = '''1 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBadNBallots(self):
        "exception if too few ballots"
        b = '''3 2 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testDupeCand(self):
        "exception candidate duplicated"
        b = '''3 2 4 1 2 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testJammedCand(self):
        "exception candidates jammed together"
        b = '''3 2 4 1 2 2 0 2 3 0 0 "Castor""Pollux""Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testInitOneLine(self):
        "normal init: 2 seats (no newlines)"
        self.assertEqual(ElectionProfile(data=p_42a).nSeats, 2)

    def testInitComment(self):
        "normal init: 2 seats (comment)"
        b = '''3 2 4 1 2 0 2 3 0 0 /* comment */ "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertEqual(ElectionProfile(data=b).nSeats, 2)

    def testInitNestedComment(self):
        "normal init: 2 seats (nested comment)"
        b = '''3 2 4 1 2 0 2 3 0 0 /* nested /*comment */ */ "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertEqual(ElectionProfile(data=b).nSeats, 2)

    def testInitOneTokenComment(self):
        "normal init: 2 seats (single-token comment)"
        b = '''3 2 4 1 2 0 2 3 0 0 /* nested /*comment*/ */ "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertEqual(ElectionProfile(data=b).nSeats, 2)

    def testInitHashComment(self):
        "normal init: 2 seats (hash comment)"
        b = '''3 2 4 1 2 0 2 3 0 0 # comment\n "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertEqual(ElectionProfile(data=b).nSeats, 2)

    def testInitHashInQuote(self):
        "normal init: 2 seats (ignore hash in title)"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen # should tie"'''
        self.assertEqual(ElectionProfile(data=b).nSeats, 2)

    def testInitHashEndsQuote(self):
        "normal init: 2 seats (ignore hash at end of title)"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should #tie"'''
        self.assertEqual(ElectionProfile(data=b).nSeats, 2)

    def testInitTitle(self):
        "normal init: title set"
        t1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        t2 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" junk'''
        self.assertEqual(ElectionProfile(data=t1).title, 'Pollux and Helen should tie')
        self.assertEqual(ElectionProfile(data=t2).title, 'Pollux and Helen should tie')

    def testInitSourceComment(self):
        "normal init: source & comment set"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "title" "source less" "comment more"'''
        b2 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "title" "source less'''
        b3 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "title" "source less" "comment more'''
        b4 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "title" "source less" junk'''
        b5 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "title" "source less" "comment more" junk'''
        b6 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "title" "source less"'''
        self.assertEqual(ElectionProfile(data=b1).title, 'title')
        self.assertEqual(ElectionProfile(data=b1).source, 'source less')
        self.assertEqual(ElectionProfile(data=b6).source, 'source less')
        self.assertEqual(ElectionProfile(data=b4).source, 'source less')
        self.assertEqual(ElectionProfile(data=b1).comment, 'comment more')
        self.assertEqual(ElectionProfile(data=b5).comment, 'comment more')
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b2)
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b3)

    def testInitnBallots(self):
        "normal init: 6 ballots"
        self.assertEqual(ElectionProfile(data=p_42).nBallots, 6)

    def testInitnBallotLines(self):
        "normal init: 2 ballot lines"
        self.assertEqual(len(ElectionProfile(data=p_42).ballotLines), 2)

    def testInitnSeats(self):
        "0 > nSeats <=candidates"
        p_42s1 = '''4 0 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Bob" "Pollux and Helen should tie"'''
        p_42s2 = '''4 5 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Bob" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42s1)
        self.assertRaises(ElectionProfileError, ElectionProfile, data=p_42s2)

    def testInitNoWithdrawn(self):
        "normal init: 0 withdrawn"
        self.assertEqual(len(ElectionProfile(data=p_42a).withdrawn), 0)

    p_42w = '''4 2 -4 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Bob" "Pollux and Helen should tie"'''
    p_42w3 = '''4 2 -3 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Bob" "Pollux and Helen should tie"'''

    def testInitOneWithdrawn(self):
        "normal init: 1 withdrawn"
        self.assertEqual(len(ElectionProfile(data=self.p_42w).withdrawn), 1)

    def testInitOneWithdrawnEligible(self):
        "normal init: 1 withdrawn"
        self.assertEqual(len(ElectionProfile(data=self.p_42w).eligible), 3)

    def testInitBallotCount(self):
        "effect of withdrawals on ballot count"
        self.assertEqual(ElectionProfile(data=p_42a).nBallots, 6)
        self.assertEqual(ElectionProfile(data=self.p_42w).nBallots, 6)
        self.assertEqual(ElectionProfile(data=self.p_42w3).nBallots, 4)

    def testInitBobName(self):
        "normal init: name of candidate"
        self.assertEqual(ElectionProfile(data=self.p_42w).candidateName[4], 'Bob')

    def testInitBobOrder(self):
        "normal init: order of candidate"
        self.assertEqual(ElectionProfile(data=self.p_42w).candidateOrder[4], 4)

    def testBadNcand(self):
        "exception bad candidate format"
        b = '''3x 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBadNSeats(self):
        "exception bad seats format"
        b = '''3 2x 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBadWithdrawn(self):
        "exception bad withdrawn"
        b = '''3 2 -2x 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBadMultiplier(self):
        "exception ballot multiplier"
        b = '''3 2 4 1 2 0 2x 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBadCid(self):
        "exception bad cid"
        b1 = '''3 2 4 1 2 0 2 3x 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
        b2 = '''3 2 4 1 2 0 2 4 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b1)
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b2)

    def testBadName(self):
        "exception bad candidate name"
        b = '''3 2 4 1 2 0 2 3 0 0 Castor" "Pollux" "Helen" "Pollux and Helen should tie" '''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBadTitle(self):
        "exception bad title"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie '''
        b2 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" Pollux and Helen should tie" '''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b1)
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b2)

    def testCandidateName(self):
        "fetch a candidate name"
        p = ElectionProfile(data=p_42a)
        self.assertEqual(p.candidateName[1], 'Castor')

    def testCandidateOrder(self):
        "fetch a candidate order"
        p = ElectionProfile(data=p_42a)
        self.assertEqual(p.candidateOrder[1], 1)

    def testBadFile(self):
        "exception: bad file name"
        self.assertRaises(ElectionProfileError, ElectionProfile, path='nofileatall')

    def testNoEnd(self):
        "exception: no end of blt"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should...'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testInitSeatsFile(self):
        "normal init from file: 2 seats"
        path = testdir + '/blt/42.blt'
        self.assertEqual(ElectionProfile(path=path).nSeats, 2)

    def testCompareFile(self):
        "normal init from file: 2 seats"
        path = testdir + '/blt/42.blt'
        pd = ElectionProfile(data=p_42)
        pp = ElectionProfile(path)
        self.assertFalse(pp.compare(pd), 'compare election 42 from file vs data blob')

class OptionNickTest(unittest.TestCase):
    "test blt option [nick...]"
    
    def testNick1(self):
        "test basic nicknames"
        b0 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b1 = '''3 2 [nick a b c ] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 [nick a b c] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p0 = ElectionProfile(data=b0)
        self.assertEqual(len(p0.nickName), 3)
        p1 = ElectionProfile(data=b1)
        self.assertEqual(len(p1.nickName), 3)
        p2 = ElectionProfile(data=b2)
        self.assertEqual(len(p2.nickName), 3)
        self.assertEqual(len(p2._nickCid), 3)
        for i in xrange(len(p1.ballotLines)):
            self.assertEqual(p1.ballotLines[i].multiplier, p2.ballotLines[i].multiplier)
            self.assertEqual(p1.ballotLines[i].ranking, p2.ballotLines[i].ranking)
            self.assertEqual(p1.ballotLines[i].multiplier, p0.ballotLines[i].multiplier)
            self.assertEqual(p1.ballotLines[i].ranking, p0.ballotLines[i].ranking)

    def testNick2(self):
        "test invalid nicknames"
        b1 = '''3 2 [nick a b c d ] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b1)
        b2 = '''3 2 [nick a b 3 ] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b2)
        b3 = '''3 2 [nick a b a ] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b3)
        b4 = '''3 2 [nick] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b4)

class OptionTieTest(unittest.TestCase):
    "test blt option [tie...]"
    
    def testTiedOrder(self):
        "test tied order"
        b = '''3 2 [tie 3 2 1 ] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p = ElectionProfile(data=b)
        self.assertEqual(len(p.tieOrder), 3)

    def testTiedOrder0(self):
        "test tied order"
        b = '''3 2 [tie 3 2 1] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p = ElectionProfile(data=b)
        self.assertEqual(len(p.tieOrder), 3)

    def testTiedOrder1(self):
        "test bad option"
        b = '''3 2 [x 3 2 1 ] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testTiedOrder2(self):
        "test bad [tie: too few elements"
        b = '''3 2 [tie 3 2 ] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testTiedOrder3(self):
        "test bad [tie: cid out of range"
        b = '''3 2 [tie 3 2 4 ] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testTiedOrder4(self):
        "test bad [tie: non-numeric cid"
        b = '''3 2 [tie 3 2 1x ] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

class OptionDroopTest(unittest.TestCase):
    "test blt option [droop ...]"

    def testDroopOptionCount(self):
        "set arithmetic options"
        b0 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertEqual(len(ElectionProfile(data=b0).options), 0)
        b1 = '''3 2 [droop arithmetic=fixed] 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertEqual(len(ElectionProfile(data=b1).options), 1)
        b2 = '''3 2 [droop arithmetic=fixed precision=6] 4 1 2 0 2 3 0 0 
            "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p = ElectionProfile(data=b2)
        self.assertEqual(len(p.options), 2)
        self.assertEqual(p.options[0], 'arithmetic=fixed')
        self.assertEqual(p.options[1], 'precision=6')

class BallotIDTest(unittest.TestCase):
    "test ballot IDs"
    
    def testBallotID1(self):
        "test basic ballot ID parsing"
        b = '''3 2 (id1) 1 2 0 (id2) 1 2 0 (id3 ) 1 2 0 ( id4) 1 2 0 ( id5 ) 3 0 (id6) 3 0 0 "A" "B" "C" "Title"'''
        p = ElectionProfile(data=b)
        self.assertEqual(len(p.ballotLines), 6)

    def testBallotID2(self):
        "test ballot ID: duplicate"
        b = '''3 2 (id1) 1 2 0 (id1) 1 2 0 (id3 ) 1 2 0 ( id4) 1 2 0 ( id5 ) 3 0 (id6) 3 0 0 "A" "B" "C" "Title"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBallotID3(self):
        "test ballot ID: missing one"
        b = '''3 2 (id1) 1 2 0 (id2) 1 2 0 (id3 ) 1 2 0 ( id4) 1 2 0 ( id5 ) 3 0 1 3 0 0 "A" "B" "C" "Title"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBallotID4(self):
        "test ballot ID: collision after stripping"
        b = '''3 2 (id1) 1 2 0 (id2) 1 2 0 (id3 ) 1 2 0 ( id4) 1 2 0 ( id1 ) 3 0 (id6) 3 0 0 "A" "B" "C" "Title"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

class BallotEqualRankTest(unittest.TestCase):
    "test ballots with equal rankings"
    
    def testBallotEQ1(self):
        "verify profile with no equal rankings"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p = ElectionProfile(data=b)
        self.assertEqual(len(p.ballotLines), 2)
        self.assertEqual(len(p.ballotLinesEqual), 0)

    def testBallotEQ2(self):
        "verify profile with an equal ranking"
        b = '''3 2 4 1 2 0 2 2=3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p = ElectionProfile(data=b)
        self.assertEqual(len(p.ballotLines), 1)
        self.assertEqual(len(p.ballotLinesEqual), 1)

    def testBallotEQ3(self):
        "verify profile with a bad ranking"
        b = '''3 2 4 1 2 0 2 2==3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBallotEQ4(self):
        "verify profile with a bad ranking"
        b = '''3 2 4 1 2 0 2 2=3= 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBallotEQ5(self):
        "verify profile with a bad ranking"
        b = '''3 2 4 1 2 0 2 =2 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBallotEQ6(self):
        "verify profile with equality and a duplicate ranking"
        b = '''3 2 4 1 2 0 2 2=2 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBallotEQ7(self):
        "verify profile with equality and a duplicate ranking"
        b = '''3 2 4 1 2 0 2 2=3 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        self.assertRaises(ElectionProfileError, ElectionProfile, data=b)

    def testBallotEQ8(self):
        "test profile compare with equal rankings"
        b1 = '''3 2 4 1 2=3 0 2 2=3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 4 1 2=3 0 2 2=3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b3 = '''3 2 3 1 2=3 0 3 2=3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b4 = '''3 2 4 1 2=3 0 2 2=1 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p1 = ElectionProfile(data=b1)
        p2 = ElectionProfile(data=b2)
        self.assertFalse(p1.compare(p2))
        p3 = ElectionProfile(data=b3)
        p4 = ElectionProfile(data=b4)
        self.assertTrue(p1.compare(p3))
        self.assertTrue(p1.compare(p4))

class Utf8Test(unittest.TestCase):
    "test utf-8 blt input"
    
    def testUTF1(self):
        "utf-8 names, title"
        self.assertEqual(ElectionProfile(data=p_42u).nSeats, 2)

    def testUTF2(self):
        "utf-8 names, title"
        self.assertEqual(ElectionProfile(data=p_42u).title, 'Pøllux and Hélen should tie')

    def testUTF3(self):
        "utf-8 file"
        path = testdir + '/blt/42u.blt'
        self.assertEqual(ElectionProfile(path=path).title, 'Pøllüx and Hélen should tie')

    def testUTF4(self):
        "utf-8 file with bom"
        path = testdir + '/blt/42ubom.blt'
        self.assertEqual(ElectionProfile(path=path).title, 'Pøllüx and Hélen should tie')

if __name__ == '__main__':
    unittest.main()
