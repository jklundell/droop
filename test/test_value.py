''' Unit test for value module'''
import unittest
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))
import modules.value

class ValueTest(unittest.TestCase):
    "tests for modules.value"
    
    def testValueInitRational(self):
        "class Rational if precision & guard are None"
        self.assertEqual(modules.value.Value.ArithmeticClass(None, None),
            modules.value.Rational)

    def testValueInitRationalDefault(self):
        "default class Rational"
        self.assertEqual(modules.value.Value.ArithmeticClass(),
            modules.value.Rational)

    def testValueInitFixed(self):
        "Fixed if there's a precision"
        self.assertEqual(modules.value.Value.ArithmeticClass(1),
            modules.value.Fixed)


class ValueTestFixed6(unittest.TestCase):
    p = 6
    g = 0
    def setUp(self):
        "initialize fixed point six places"
        modules.value.Value.ArithmeticClass(self.p, self.g)
        
    def testExact(self):
        "Not exact if there's a precision"
        self.assertEqual(modules.value.Fixed.exact, False)

    def testScalep(self):
        "Scale 10^6 if precision is 6"
        self.assertEqual(modules.value.Fixed._Fixed__scalep, 10**self.p)

class ValueTestQX9(unittest.TestCase):
    p = 9
    g = p
    def setUp(self):
        "initialize quasi-exact 9.None s/b 9.9"
        modules.value.Value.ArithmeticClass(self.p)
        
    def testExact(self):
        "quasi-exact is exact"
        self.assertEqual(modules.value.Fixed.exact, True)

    def testScale(self):
        "scale is a function of precision and guard"
        self.assertEqual(modules.value.Fixed._Fixed__scale, 10**(self.p+self.g))

    def testGeps(self):
        "geps is a function of guard"
        self.assertEqual(modules.value.Fixed._Fixed__geps, 10**self.g/10)

    def testBadP(self):
        "test illegal precision"
        self.assertEqual(modules.value.Fixed.exact, True)

class ValueTestBadP(unittest.TestCase):

    def testBadP(self):
        "TypeError"
        self.assertRaises(TypeError('value.Fixed: precision must be an int'), modules.value.Value.ArithmeticClass(5.5))

if __name__ == '__main__':
    unittest.main()