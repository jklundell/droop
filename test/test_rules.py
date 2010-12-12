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
from __future__ import absolute_import
import unittest

from . import common  # to set sys.path
from droop import electionRuleNames, electionRule
from droop.common import ElectionError
from droop.election import Election
from droop.profile import ElectionProfile

if common.pyflakes: # satisfy pyflakes that we're using common
    pass

class RuleInitTest(unittest.TestCase):
    "test rules.__init__"
    
    def testRuleNames(self):
        "check the list of rule names"
        self.assertTrue(len(electionRuleNames()) >= 1, 'at least one rule name')

    def testElectionNoProfile(self):
        "trying an election without a profile should fail"
        self.assertRaises(ElectionError, Election, None, dict())

    def testElectionNoRule(self):
        "trying an election without a rule should fail"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p = ElectionProfile(data=b)
        self.assertRaises(ElectionError, Election, p, dict())

    def testElectionBadRule(self):
        "trying an election with an undefined rule should fail"
        b = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        p = ElectionProfile(data=b)
        self.assertRaises(ElectionError, Election, p, dict(rule='nothing'))

class RuleTest(unittest.TestCase):
    "test rules class methods"
    
    def testMethod(self):
        "method is meek or wigm or qpq for each rule"
        for name in electionRuleNames():
            Rule = electionRule(name)
            method = Rule.method
            self.assertTrue(method in ('meek', 'wigm', 'qpq'), 'bad method "%s"' % method)

    def testReportHelps(self):
        "helps gives us back a string"
        for name in electionRuleNames():
            Rule = electionRule(name)
            helps = dict()
            Rule.helps(helps, name)
            self.assertTrue(isinstance(helps[name], str), 'expected help string for %s' % name)

if __name__ == '__main__':
    unittest.main()
