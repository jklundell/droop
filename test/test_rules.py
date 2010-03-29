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
import unittest
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))

from droop import electionRuleNames, electionRule
from droop import rules as R

class RuleInitTest(unittest.TestCase):
    "test rules.__init__"
    
    def testRuleNames(self):
        "check the list of names"
        self.assertTrue(len(electionRuleNames()) >= 4, 'at least four rule names')

    def testRuleNameMpls(self):
        "check the list of names for mpls"
        self.assertTrue('mpls' in electionRuleNames(), 'one of the rule names is mpls')

    def testElectionRule(self):
        "look up one election rule"
        from droop.rules.mpls import Rule as Mpls
        self.assertEqual(electionRule('mpls'), Mpls, 'the mpls Rule should match its name lookup')


class RuleTest(unittest.TestCase):
    "test rules class methods"
    
    def testReportModes(self):
        "reportMode is meek or wigm for each rule"
        for name in electionRuleNames():
            Rule = electionRule(name)
            reportMode = Rule.reportMode()
            self.assertTrue(reportMode in ('meek','wigm'), 'bad reportMode "%s"' % reportMode)

        
if __name__ == '__main__':
    unittest.main()