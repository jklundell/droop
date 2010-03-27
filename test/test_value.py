''' 
Unit test for value module

copyright 2010 by Jonathan Lundell
'''
import unittest
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))

from packages import values as V
from packages.values.fixed import Fixed as F
from packages.values.guarded import Guarded as G
from packages.values.rational import Rational as R

class ValueTest(unittest.TestCase):
    "test value-class initialization"
    
    def testValueInitRational(self):
        "class Rational if arithmetic=rational"
        self.assertEqual(V.ArithmeticClass(dict(arithmetic='rational')), R)

    def testValueInitRationalDefault(self):
        "default class Guarded"
        self.assertEqual(V.ArithmeticClass(), G)

    def testBadArithmetic(self):
        "try unknown arithmetic"
        self.assertRaises(V.arithmeticValuesError, V.ArithmeticClass, dict(arithmetic='saywhat'))

    def testBadP1(self):
        "precision must be an int"
        self.assertRaises(TypeError, V.ArithmeticClass, dict(precision=5.5))

    def testBadP2(self):
        "precision must be >= 0"
        self.assertRaises(TypeError, V.ArithmeticClass, dict(precision=-1))

    def testBadG1(self):
        "guard must be an int"
        self.assertRaises(TypeError, V.ArithmeticClass, 5, 5.5)

    def testBadG2(self):
        "guard must be >= 0"
        self.assertRaises(TypeError, V.ArithmeticClass, 5, -1)

class ValueTestFixed6(unittest.TestCase):
    p = 6
    g = 0
    A = None
    def setUp(self):
        "initialize fixed point six places"
        self.A = V.ArithmeticClass(options=dict(arithmetic='fixed', precision=self.p, guard=self.g))
        
    def testFixed6(self):
        "simple assertions"
        self.assertEqual(self.A.name, 'fixed')               # Fixed.name
        self.assertEqual(self.A.exact, False)                # Fixed.exact
        self.assertEqual(self.A.precision, self.p)           # Fixed.precision
        self.assertEqual(self.A._Fixed__scale, 10**self.p)   # Fixed.__scale
        self.assertEqual(self.A(0)._value, 0)                # 0
        self.assertEqual(self.A(1)._value, 10**self.p)       # 1
        self.assertEqual(self.A(100)._value, 100*10**self.p) # 100
        self.assertEqual((self.A(1)/self.A(10))._value, 10**(self.p-1))  # 1/10

class ValueTestRounding(unittest.TestCase):
    "test rounding of fixed values"
    p = 3
    g = 0
    def setUp(self):
        "initialize fixed class"
        V.ArithmeticClass(options=dict(arithmetic='fixed', precision=self.p, guard=self.g))
        
    def testRoundFloor(self):
        "default rounding is truncation/floor"
        self.assertEqual((F(1)/F(3))._value, 333)

    def testRoundDown(self):
        "down is same as default"
        self.assertEqual(F.div(F(1),F(3),round='down')._value, 333)

    def testRoundUp(self):
        "up is bigger by an epsilon"
        self.assertEqual(F.div(F(1),F(3),round='up')._value, 334)

    def testRoundDownExact(self):
        "no rounding if exact result"
        self.assertEqual(F.div(F(2),F(4),round='down')._value, 500)

    def testRoundUpExact(self):
        "up is bigger by an epsilon but not if exact result"
        self.assertEqual(F.div(F(2),F(4),round='up')._value, 500)

    def testRoundBad(self):
        "round= must be up or down"
        self.assertRaises(ValueError, F.div, F(1),F(3),round='bad')

    def testRoundNone(self):
        "round= must be present"
        self.assertRaises(ValueError, F.div, F(1),F(3))

class ValueTestGuarded9(unittest.TestCase):
    p = 9
    g = p
    A = None
    def setUp(self):
        "initialize quasi-exact 9.None s/b 9.9"
        self.A = V.ArithmeticClass(options=dict(arithmetic='guarded', precision=self.p))
        
    def testExact(self):
        "quasi-exact is exact"
        self.assertEqual(self.A.exact, True)

    def testScale(self):
        "scale is a function of precision and guard"
        self.assertEqual(self.A._Guarded__scale, 10**(self.p+self.g))

    def testGeps(self):
        "geps is a function of guard"
        self.assertEqual(self.A._Guarded__geps, 10**self.g/10)

    def testBadP(self):
        "test illegal precision"
        self.assertEqual(self.A.exact, True) # TBD

if __name__ == '__main__':
    unittest.main()