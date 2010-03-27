''' 
Unit test for value module

copyright 2010 by Jonathan Lundell
'''
import unittest
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))

from packages import rules as R
from packages.rules.meek import Rule as Meek
from packages.rules.mpls import Rule as Mpls
from packages.rules.wigm import Rule as WIGM


class RuleTest(unittest.TestCase):
    "test rule-class initialization"
    
    def testMeekReportMode(self):
        "meek.Rule report mode is meek"
        self.assertEqual(Meek.reportMode(), 'meek')

if __name__ == '__main__':
    unittest.main()