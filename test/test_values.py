#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' 
Unit test for droop.value package

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
from droop.common import UsageError
from droop.options import Options
from droop import values as V
from droop.values.fixed import Fixed as F
from droop.values.guarded import Guarded as G
from droop.values.rational import Rational as R

if common.pyflakes: # satisfy pyflakes that we're using common
    pass

class ValueTest(unittest.TestCase):
    "test value-class initialization"
    
    #  general initialization
    #
    def testBadArithmetic(self):
        "try unknown arithmetic"
        self.assertRaises(V.ArithmeticValuesError, V.ArithmeticClass, Options(dict(arithmetic='saywhat')))

    def testValueInitRationalDefault(self):
        "default class Guarded"
        self.assertEqual(V.ArithmeticClass(Options(dict(precision=8))), G)

    def testValueInitFixed(self):
        "class Fixed if arithmetic=fixed"
        self.assertEqual(V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=8))), F)

    def testBadFixedA(self):
        "fixed called directly must be fixed or integer"
        self.assertRaises(UsageError, F.initialize, Options(dict(arithmetic='bill')))

    def testValueInitRational(self):
        "class Rational if arithmetic=rational"
        self.assertEqual(V.ArithmeticClass(Options(dict(arithmetic='rational'))), R)

    def testBadP1(self):
        "precision must be an int"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(precision=5.5)))

    def testBadP2(self):
        "precision must be >= 0"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(precision=-1)))

    def testBadG1(self):
        "guard must be an int"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(precision=5, guard=5.5)))

    def testBadG2(self):
        "guard must be >= 0"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(precision=5, guard=-1)))

    #  Fixed initialization
    #
    def testFixedIntegerP0(self):
        "fixed=integer yields precision 0"
        V.ArithmeticClass(Options(dict(arithmetic='integer')))
        self.assertEqual(F.precision, 0)

    def testBadFixedPx(self):
        "fixed precision must be numeric"
        self.assertRaises(UsageError, F.initialize, Options(dict(arithmetic='fixed', precision='abc')))

    def testBadFixedDx(self):
        "fixed display must be numeric"
        self.assertRaises(UsageError, F.initialize, Options(dict(arithmetic='fixed', precision=9, display='abc')))

    def testBadFP1(self):
        "fixed precision must be an int"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='fixed', precision=5.5)))

    def testBadFP2(self):
        "fixed precision must be >= 0"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='fixed', precision=-1)))

    def testFixedInteger(self):
        "fixed precision 0 means integer"
        V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=0)))
        self.assertEqual(F.tag(), 'integer')

    def testFixedDisplay1(self):
        "fixed display must be <= precision"
        V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=6, display=7)))
        self.assertEqual(F.display, 6)
        self.assertTrue(F.info.find('display') < 0)

    def testFixedDisplay2(self):
        "fixed display != precision gets a mention in info"
        V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=6, display=5)))
        self.assertTrue(F.info.find('display') > 0)

    def testFixedDisplay3(self):
        "fixed display < precision rounds properly"
        V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=6, display=6)))
        self.assertEqual(str(F(20)/F(3)), '6.666666')
        V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=7, display=6)))
        self.assertEqual(str(F(20)/F(3)), '6.666667')

class ValueTestFixed6(unittest.TestCase):
    "Fixed with precision=6"
    p = 6
    g = 0
    A = None
    def setUp(self):
        "initialize fixed point six places"
        self.A = V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=self.p, guard=self.g)))
        
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
        x = self.A(1)
        y = self.A(2)
        self.assertEqual(-x, x-y)
        self.assertEqual(+x, y-x)
        self.assertEqual(abs(x-y), x)
        self.assertEqual(y/1, y/x)
        self.assertRaises(ValueError, self.A.mul, x, y, 'bad')
        self.assertRaises(ValueError, self.A.muldiv, x, y, y, 'bad')
        f13 = F(1)/F(3)
        f15 = F(1)/F(5)
        f17 = F(1)/F(7)
        self.assertTrue(F.muldiv(f13, f15, f17, round='down') > f13*f15/f17)
        self.assertTrue(F.muldiv(f13, f15, f17, round='up') > F.muldiv(f13, f15, f17, round='down'))
        self.assertEqual(str(f13*f15/f17), '0.466662')
        self.assertEqual(str(F.muldiv(f13, f15, f17, round='down')), '0.466666')
        self.assertEqual(str(F.muldiv(f13, f15, f17, round='up')), '0.466667')
        self.assertTrue(x != y)
        self.assertEqual(str(x/y), '0.500000')

    def testSetvalFixed6(self):
        "set a fixed value directly"
        A = V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=6)))
        f = A(123456, True)
        self.assertEqual(repr(A(f)), 'Fixed(123456,True)')
        self.assertEqual(A(1000000, True), A(1))

    def testReprFixed6(self):
        "repr is the underlying _value"
        A = V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=6)))
        self.assertEqual(repr(A(1)), 'Fixed(1000000,True)')

class ValueTestFixed0(unittest.TestCase):
    "Fixed with precision=0 is Integer"
    p = 0
    g = 0
    A = None
    def setUp(self):
        "initialize fixed point 0 places"
        self.A = V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=self.p, guard=self.g)))
        
    def testFixed0(self):
        "simple assertions"
        self.assertEqual(self.A.name, 'integer')               # Fixed.name
        x = F(1)
        self.assertEqual(str(x), '1')

    def testReprFixed0(self):
        "repr is the underlying _value"
        A = V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=self.p)))
        self.assertEqual(repr(A(1)), '1')
        A = V.ArithmeticClass(Options(dict(arithmetic='integer')))
        self.assertEqual(repr(A(1)), '1')

class ValueTestGuarded0(unittest.TestCase):
    "Guarded with guard=0 should match Fixed"
    p = 6
    g = 0
    def setUp(self):
        "initialize guarded and fixed to no guard"
        F.initialize(Options(dict(arithmetic='fixed', precision=self.p, guard=self.g)))
        G.initialize(Options(dict(arithmetic='guarded', precision=self.p, guard=self.g)))

    def testG0(self):
        "basic equalities"
        f1 = F(1)
        f2 = F(2)
        f3 = F(3)
        f7 = F(7)
        g1 = G(1)
        g2 = G(2)
        g3 = G(3)
        g7 = G(7)
        self.assertEqual(str(f1), str(g1))
        self.assertEqual(str(f1/f3), str(g1/g3))
        self.assertEqual(str(f2/f3), str(g2/g3))
        self.assertEqual(F.mul(f2, f3, round='down'), G.mul(g2, g3, round='down'))
        self.assertEqual(F.mul(f2, f3, round='up'), G.mul(g2, g3, round='up'))
        self.assertEqual(F.div(f2, f3, round='down'), G.div(g2, g3, round='down'))
        self.assertEqual(F.div(f2, f3, round='up'), G.div(g2, g3, round='up'))
        self.assertEqual(F.muldiv(f2, f3, f7, round='down'), G.muldiv(g2, g3, g7, round='down'))
        self.assertEqual(F.muldiv(f2, f3, f7, round='up'), G.muldiv(g2, g3, g7, round='up'))

class ValueTestGuardedRat(unittest.TestCase):
    "Guarded should match Rational given equivalent display precision and enough guard"
    p = 18
    g = 9
    def setUp(self):
        "initialize guarded and rational"
        R.initialize(Options(dict(arithmetic='rational', display=self.p)))
        G.initialize(Options(dict(arithmetic='guarded', precision=self.p, guard=self.g)))

    def testGR(self):
        "basic equalities"
        r1 = R(1)
        r2 = R(2)
        r3 = R(3)
        r7 = R(7)
        g1 = G(1)
        g2 = G(2)
        g3 = G(3)
        g7 = G(7)
        self.assertEqual(str(R(r1)), str(g1))
        self.assertEqual(str(R(r1/r3)), str(g1/g3))
        self.assertEqual(str(R(r2/r3)), str(g2/g3))
        self.assertEqual(str(R(R.mul(r2, r3))), str(G.mul(g2, g3)))
        self.assertEqual(str(R(R.div(r2, r3))), str(G.div(g2, g3)))
        self.assertEqual(str(R(R.muldiv(r2, r3, r7))), str(G.muldiv(g2, g3, g7)))

class ValueTestRounding(unittest.TestCase):
    "test rounding of fixed values"
    p = 3
    g = 0
    def setUp(self):
        "initialize fixed class"
        V.ArithmeticClass(Options(dict(arithmetic='fixed', precision=self.p, guard=self.g)))
        
    def testRoundFloor(self):
        "default rounding is truncation/floor"
        self.assertEqual((F(1)/F(3))._value, 333)

    def testRoundDown(self):
        "down is same as default"
        self.assertEqual(F.div(F(1), F(3), round='down')._value, 333)

    def testRoundUp(self):
        "up is bigger by an epsilon"
        self.assertEqual(F.div(F(1), F(3), round='up')._value, 334)

    def testRoundDownExact(self):
        "no rounding if exact result"
        self.assertEqual(F.div(F(2), F(4), round='down')._value, 500)

    def testRoundUpExact(self):
        "up is bigger by an epsilon but not if exact result"
        self.assertEqual(F.div(F(2), F(4), round='up')._value, 500)

    def testRoundBad(self):
        "round= must be up or down"
        self.assertRaises(ValueError, F.div, F(1), F(3), round='bad')

    def testRoundNone(self):
        "round= must be present"
        self.assertRaises(ValueError, F.div, F(1), F(3))

class ValueTestGuarded9(unittest.TestCase):
    "guarded-specific unit tests"

    def testExact(self):
        "guarded is exact"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9)))
        self.assertEqual(A.exact, True)

    def testScale(self):
        "scale is a function of precision and guard"
        p = 9
        g = p
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=p)))
        self.assertEqual(A._Guarded__scale, 10**(p+g))

    def testGeps(self):
        "geps is a function of guard"
        p = 9
        g = p
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=p)))
        self.assertEqual(A._Guarded__geps, 10**g/2)

    def testBadPrecision(self):
        "test illegal precision"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision=1.1)))
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision=-1)))
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision='abc')))

    def testBadGuard(self):
        "test illegal guard"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision=4, guard=1.1)))
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision=4, guard=-1)))
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision=4, guard='abc')))

    def testBadDisplay(self):
        "test illegal display"
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision=4, display=1.1)))
        self.assertRaises(UsageError, V.ArithmeticClass, Options(dict(arithmetic='guarded', precision=4, display=-1)))
        self.assertRaises(UsageError, V.ArithmeticClass, 
            Options(dict(arithmetic='guarded', precision=4, display='abc')))

    def testDisplay(self):
        "display defaults to precision"
        p = 5
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=p)))
        self.assertEqual(A.display, p)
        self.assertEqual(str(A(20)/A(3)), '6.66667')

    def testBigDisplay(self):
        "display is limited to precision+guard"
        p = 5
        g = 6
        d = p + g + 1
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=p, guard=g, display=d)))
        self.assertEqual(A.display, p+g)
        self.assertEqual(str(A(20)/A(3)), '6.66666_666666')

    def testBadArithmetic(self):
        "test illegal arithmetic"
        self.assertRaises(UsageError, G.initialize, Options(dict(arithmetic='fixed', precision=4)))

    def testUnaryOps(self):
        "test unary + and -"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=4)))
        x = A(1)
        y = A(2)
        self.assertEqual(x-y, -x)
        self.assertEqual(y-x, +x)
        self.assertEqual(abs(x-y), x)

    def testDivInt(self):
        "test guarded/int"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9)))
        x = A(2)
        y = A(3)
        self.assertEqual(x/y, x/3)

    def testMulInt(self):
        "test guarded*int"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9)))
        x = A(2)
        y = A(3)
        self.assertEqual(x*y, x*3)

    def testNoHash(self):
        "test guarded/int"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9)))
        x = A(2)
        self.assertRaises(NotImplementedError, hash, x)

    def testMulDiv(self):
        "guarded muldiv"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9)))
        f13 = A(1)/A(3)
        f15 = A(1)/A(5)
        f17 = A(1)/A(7)
        self.assertEqual(A.muldiv(f13, f15, f17), f13*f15/f17)
        self.assertEqual(str(f13*f15/f17), '0.466666667')
        self.assertEqual(str(A.muldiv(f13, f15, f17)), '0.466666667')

    def testMulDiv0(self):
        "guarded muldiv with g=0"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9, guard=0)))
        f13 = A(1)/A(3)
        f15 = A(1)/A(5)
        f17 = A(1)/A(7)
        self.assertEqual(A.muldiv(f13, f15, f17)._value, (f13*f15/f17)._value+5)
        self.assertEqual(A.muldiv(f13, f15, f17, round='down')._value, (f13*f15/f17)._value+5)
        self.assertEqual(A.muldiv(f13, f15, f17, round='up')._value, (f13*f15/f17)._value+6)
        self.assertEqual(str(f13*f15/f17), '0.466666664')
        self.assertEqual(str(A.muldiv(f13, f15, f17)), '0.466666669')

    def testRepr(self):
        "repr is the underlying _value"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9)))
        self.assertEqual(repr(A(1)), 'Guarded(1000000000000000000,True)')

    def testNe(self):
        "not equal"
        A = V.ArithmeticClass(Options(dict(arithmetic='guarded', precision=9)))
        self.assertFalse(A(1)!=A(1))

class ValueTestRational(unittest.TestCase):
    "rational-specific unit tests"

    f13 = R(1)/R(3)
    f15 = R(1)/R(5)
    f17 = R(1)/R(7)

    def testRat1(self):
        "no loss of precision"
        self.assertEqual(self.f13 * R(3), R(1))
        
    def testMulDiv(self):
        "rational muldiv is the same as multiply followed by divide"
        self.assertEqual(R.muldiv(self.f13, self.f15, self.f17), self.f13*self.f15/self.f17)
    
class ValueTestHelps(unittest.TestCase):
    "test the helps function"
    def testHelps(self):
        "helps should fill in a dict with entries for arithmetic and its methods"
        helps = dict()
        V.helps(helps)
        self.assertTrue(len(helps['arithmetic']) > 10, 'arithmetic help string should exist')
        self.assertTrue(len(helps['rational']) > 10, 'rational help string should exist')
        self.assertTrue(len(helps['fixed']) > 10, 'fixed help string should exist')
        self.assertTrue(len(helps['guarded']) > 10, 'guarded help string should exist')


if __name__ == '__main__':
    unittest.main()
