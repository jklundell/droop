''' 
Unit test for value module

copyright 2010 by Jonathan Lundell
'''
import unittest
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))

from packages import electionRuleNames, electionRule
from packages import rules as R

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
        from packages.rules.mpls import Rule as Mpls
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