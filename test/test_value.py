''' 
Unit test for value module

copyright 2010 by Jonathan Lundell
'''
import unittest
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))
import modules.value

# shortcuts for the value classes
V = modules.value.Value
R = modules.value.Rational
F = modules.value.Fixed

class ValueTest(unittest.TestCase):
    "test value-class initialization"
    
    def testValueInitRational(self):
        "class Rational if precision & guard are None"
        self.assertEqual(V.ArithmeticClass(dict(arithmetic='rational')), R)

    def testValueInitRationalDefault(self):
        "default class Fixed"
        self.assertEqual(V.ArithmeticClass(), F)

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
    def setUp(self):
        "initialize fixed point six places"
        V.ArithmeticClass(options=dict(arithmetic='fixed', precision=self.p, guard=self.g))
        
    def testFixed6(self):
        "simple assertions"
        self.assertEqual(F.name, 'fixed')               # Fixed.name
        self.assertEqual(F.exact, False)                # Fixed.exact
        self.assertEqual(F._Fixed__precision, self.p)   # Fixed.__precision
        self.assertEqual(F._Fixed__scalep, 10**self.p)  # Fixed.__scalep
        self.assertEqual(F(0)._value, 0)                # 0
        self.assertEqual(F(1)._value, 10**self.p)       # 1
        self.assertEqual(F(100)._value, 100*10**self.p) # 100
        self.assertEqual((F(1)/F(10))._value, 10**(self.p-1))  # 1/10

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

class ValueTestQX9(unittest.TestCase):
    p = 9
    g = p
    def setUp(self):
        "initialize quasi-exact 9.None s/b 9.9"
        V.ArithmeticClass(options=dict(precision=self.p))
        
    def testExact(self):
        "quasi-exact is exact"
        self.assertEqual(F.exact, True)

    def testScale(self):
        "scale is a function of precision and guard"
        self.assertEqual(F._Fixed__scale, 10**(self.p+self.g))

    def testGeps(self):
        "geps is a function of guard"
        self.assertEqual(F._Fixed__geps, 10**self.g/10)

    def testBadP(self):
        "test illegal precision"
        self.assertEqual(F.exact, True)

if __name__ == '__main__':
    unittest.main()