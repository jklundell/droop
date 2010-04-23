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
import sys, os, re
testdir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.normpath(os.path.join(testdir, '..'))
if basedir not in sys.path: sys.path.insert(0, os.path.normpath(basedir))

import droop
from droop.election import Election
from droop.profile import ElectionProfile
from droop import rules as R

class ElectionInitTest(unittest.TestCase):
    '''
    test Election.__init__
    
    Create an Election instance from a simple profile 
    and the Minneapolis rule and test its basic initialization,
    and that it elects the specified number of seats.
    '''
    
    def setUp(self):
        "initialize profile and rule"
        path = testdir + '/blt/42.blt'
        self.Profile = ElectionProfile(path)
        self.Rule = R.mpls.Rule
        self.options = dict()
        self.E = Election(self.Rule, self.Profile, self.options)

    def testElectionInit(self):
        "check that election is initialized"
        self.assertTrue(self.E.rule == self.Rule, 'bad rule class')
        self.assertEqual(len(self.options), 2, 'mpls should set two options')
        self.assertEqual(self.options['arithmetic'], 'fixed', 'mpls should set arithmetic=fixed')
        self.assertEqual(self.options['precision'], 4, 'mpls should set precision=4')

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

    def doCount(self, Rule, options, blt):
        "run the count and return the Election"
        p = ElectionProfile(testdir + '/blt/' + blt)
        E = Election(Rule, p, options)
        E.count()
        return E

    def testElectionCount1(self):
        "try a basic count"
        E = self.doCount(R.mpls.Rule, dict(), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionTieCount(self):
        "check a different tiebreaking order"
        E = self.doCount(R.mpls.Rule, dict(), '42t.blt')
        tieOrder = [0, 3, 2, 1]
        for c in E.candidates.values():
            self.assertEqual(c.tieOrder, tieOrder[c.order])

    def testElectionCount2(self):
        "try a bigger election"
        E = self.doCount(R.mpls.Rule, dict(), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount3(self):
        "try wigm default"
        E = self.doCount(R.wigm.Rule, dict(), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount3a(self):
        "try wigm with integer quota"
        E = self.doCount(R.wigm.Rule, dict(integer_quota='true'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount4(self):
        "try meek default"
        E = self.doCount(R.meek.Rule, dict(), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount4a(self):
        "try meek default"
        E = self.doCount(R.meek.Rule, dict(defeat_batch='none'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount5(self):
        "try meek_prf default"
        E = self.doCount(R.meek_prf.Rule, dict(), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount6(self):
        "meek-prf-basic stable state"
        E = self.doCount(R.meek_prf.Rule, dict(precision=7, omega=7), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionMpls1(self):
        "mpls: everyone elected at first"
        p_mpls1 = '''3 2 4 1 2 0 4 2 1 0 1 3 0 0 "a" "b" "c" "2 elected at first"'''
        E = Election(R.mpls.Rule, ElectionProfile(data=p_mpls1), options=dict())
        E.count()
        self.assertEqual(len(E.elected), 2)

def doDumpCompare(rule, options, file, subdir=''):
    '''
    helper: do a count and compare dump/report to reference
    '''
    if not file.endswith('.blt'):
        file += '.blt'
    base, ext = os.path.splitext(file)
        
    blt = os.path.join(testdir, 'blt', subdir, file)
    E = Election(rule, ElectionProfile(blt), options)
    E.count()
    tag = '%s-%s-%s' % (base, rule.tag(), E.V.tag())

    def readFile(path):
        "read a dump/report file"
        f = open(path, 'r')
        data = f.read()
        f.close()
        return data
        
    def writeFile(path, data):
        "write a dump/report file"
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        f = open(path, 'w')
        f.write(data)
        f.close()
        
    #  first do dump
    #
    dref = os.path.join(testdir, 'ref', 'dump', subdir, '%s.txt' % tag)
    dout = os.path.join(testdir, 'out', 'dump', subdir, '%s.txt' % tag)
    dump = E.dump()
    if not os.path.isfile(dref):
        writeFile(dref, dump)
    dumpref = readFile(dref)
    if os.path.isfile(dout):
        os.unlink(dout)
    if dump != dumpref:
        writeFile(dout, dump)
        return False

    #  same logic with report
    #
    rref = os.path.join(testdir, 'ref', 'report', subdir, '%s.txt' % tag)
    rout = os.path.join(testdir, 'out', 'report', subdir, '%s.txt' % tag)
    report = E.report()
    if not os.path.isfile(rref):
        writeFile(rref, report)
    reportref = readFile(rref)
    if os.path.isfile(rout):
        os.unlink(rout)
    # don't include version number in comparison
    report0 = re.sub(r'droop v\d+\.\d+', 'droop v0.0', report)
    reportref = re.sub(r'droop v\d+\.\d+', 'droop v0.0', reportref)
    if report0 != reportref:
        writeFile(rout, report)
        return False
    return True

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    def getDump(self, Rule, options, base):
        "run a count and return the dump"
        blt = '%s/blt/%s.blt' % (testdir, base)
        E = Election(Rule, ElectionProfile(blt), options)
        E.count()
        return E.dump()

    def testElectionDump(self):
        "try a basic count & dump"
        self.assertTrue(doDumpCompare(R.mpls.Rule, dict(), '42'), 'Minneapolis 42.blt')

    def testElectionDumpu(self):
        "try a basic count & dump with utf-8 blt"
        self.assertTrue(doDumpCompare(R.mpls.Rule, dict(), '42u'), 'Minneapolis 42u.blt')

    def testElectionDumpWarren(self):
        "try a basic count & dump"
        self.assertTrue(doDumpCompare(R.meek.Rule, dict(variant='warren'), '42'), 'Warren 42.blt')

    def testElectionDumpMPRFStable(self):
        "meek-prf-basic stable state"
        self.assertTrue(doDumpCompare(R.meek_prf.Rule, dict(precision=7, omega=7), 'SC-Vm-12'), 'meek-prf stable state')

    def testElectionDumps(self):
        "try several counts & dumps"
        blts = ('42', '42t', '42u', 'M135', '513', 'SC', 'SCw', 'SC-Vm-12')
        ruleNames = droop.electionRuleNames()
        for blt in blts:
            for name in ruleNames:
                Rule = droop.electionRule(name)
                self.assertTrue(doDumpCompare(Rule, dict(), blt), '%s %s.blt' % (Rule.info(), blt))

    def testElectionDumpRational(self):
        "try several counts & dumps with rational arithmetic"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        Rules = (R.meek.Rule, R.wigm.Rule)
        for blt in blts:
            for Rule in Rules:
                self.assertTrue(doDumpCompare(Rule, dict(arithmetic='rational'), blt), '%s %s.blt' % (Rule.info(), blt))

    def testElectionDumpFixedVsGuarded(self):
        "guarded with guard=0 should match fixed"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        Rules = (R.meek.Rule, R.wigm.Rule)
        for blt in blts:
            for Rule in Rules:
                fdump = self.getDump(Rule, dict(arithmetic='fixed', precision=6), blt)
                gdump = self.getDump(Rule, dict(arithmetic='guarded', precision=6, guard=0), blt)
                if fdump != gdump:
                    print Rule
                    print blt
                    print fdump
                    print gdump
                self.assertEqual(fdump, gdump, 'guarded with guard=0 should match fixed')

    def testElectionDumpRationalVsGuarded(self):
        "guarded should match rational"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        Rules = (R.meek.Rule, R.wigm.Rule)
        for blt in blts:
            for Rule in Rules:
                fdump = self.getDump(Rule, dict(arithmetic='rational', omega=9, display=18), blt)
                gdump = self.getDump(Rule, dict(arithmetic='guarded', precision=18, guard=9, omega=9), blt)
                self.assertEqual(fdump, gdump, 'guarded should match rational')

    def testElectionDumpRules(self):
        "run rule-specific counts"
        ruleNames = droop.electionRuleNames()
        for name in ruleNames:
            bltdir = os.path.join(testdir, 'blt', name)
            if os.path.isdir(bltdir):
                rule = droop.electionRule(name)
                for blt in [blt for blt in os.listdir(bltdir) if blt.endswith('.blt')]:
                    self.assertTrue(doDumpCompare(rule, dict(), blt, name), '%s/%s' % (name, blt))

if __name__ == '__main__':
    unittest.main()
