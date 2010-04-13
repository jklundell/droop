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

from droop.election import Election
from droop.profile import ElectionProfile
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

    def testElectionTieOrder(self):
        "test default tie order"
        E = Election(self.Rule, self.Profile, dict())
        for c in E.candidates.values():
            self.assertEqual(c.order, c.tieOrder)

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

    def testElectionTieCount(self):
        "check a different tiebreaking order"
        E = self.doCount(R.mpls.Rule, dict(), '42t.blt')
        tieOrder = [0, 3, 2, 1]
        for c in E.candidates.values():
            self.assertEqual(c.tieOrder, tieOrder[c.order])

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

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    def readFile(self, path):
        "read a dump file"
        f = open(path, 'r')
        data = f.read()
        f.close()
        return data
        
    def writeFile(self, path, data):
        "write a dump file"
        f = open(path, 'w')
        f.write(data)
        f.close()
        
    def getDump(self, Rule, options, base):
        "run a count and return the dump"
        blt = '%s/blt/%s.blt' % (testdir, base)
        E = Election(Rule, ElectionProfile(blt), options)
        E.count()
        return E.dump()

    def doDumpCompare(self, Rule, options, base):
        "run a count and compare dump/report to reference"
        blt = '%s/blt/%s.blt' % (testdir, base)
        E = Election(Rule, ElectionProfile(blt), options)
        E.count()
        tag = '%s-%s-%s' % (base, Rule.tag(), E.V.tag())

        #  first do dump
        #
        dref = '%s/ref/dump/%s.txt' % (testdir, tag)
        dout = '%s/out/dump/%s.txt' % (testdir, tag)
        dump = E.dump()
        if not os.path.isfile(dref):
            self.writeFile(dref, dump)
        dumpref = self.readFile(dref)
        if os.path.isfile(dout):
            os.unlink(dout)
        if dump != dumpref:
            self.writeFile(dout, dump)
            return False

        #  same logic with report
        #
        rref = '%s/ref/report/%s.txt' % (testdir, tag)
        rout = '%s/out/report/%s.txt' % (testdir, tag)
        report = E.report()
        if not os.path.isfile(rref):
            self.writeFile(rref, report)
        reportref = self.readFile(rref)
        if os.path.isfile(rout):
            os.unlink(rout)
        # don't include version number in comparison
        report0 = re.sub(r'droop v\d+\.\d+', 'droop v0.0', report)
        reportref = re.sub(r'droop v\d+\.\d+', 'droop v0.0', reportref)
        if report0 != reportref:
            self.writeFile(rout, report)
            return False
        return True

    def testElectionDump(self):
        "try a basic count & dump"
        self.assertTrue(self.doDumpCompare(R.mpls.Rule, dict(), '42'), 'Minneapolis 42.blt')

    def testElectionDump(self):
        "try a basic count & dump with utf-8 blt"
        self.assertTrue(self.doDumpCompare(R.mpls.Rule, dict(), '42u'), 'Minneapolis 42u.blt')

    def testElectionDumpWarren(self):
        "try a basic count & dump"
        self.assertTrue(self.doDumpCompare(R.meek.Rule, dict(variant='warren'), '42'), 'Warren 42.blt')

    def testElectionDumps(self):
        "try several counts & dumps"
        blts = ('42', '42t', '42u', 'M135', '513', 'SC', 'SC-Vm-12')
        Rules = (R.mpls.Rule, R.meek.Rule, R.wigm.Rule, R.meek_prf.Rule)
        for blt in blts:
            for Rule in Rules:
                self.assertTrue(self.doDumpCompare(Rule, dict(), blt), '%s %s.blt' % (Rule.info(), blt))

    def testElectionDumpRational(self):
        "try several counts & dumps with rational arithmetic"
        blts = ('42', '42t', '513', 'SC', 'SC-Vm-12')
        Rules = (R.meek.Rule, R.wigm.Rule)
        for blt in blts:
            for Rule in Rules:
                self.assertTrue(self.doDumpCompare(Rule, dict(arithmetic='rational'), blt), '%s %s.blt' % (Rule.info(), blt))

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

if __name__ == '__main__':
    unittest.main()