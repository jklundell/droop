'''
Guarded-precision fixed-point decimal value class
   Guarded supports quasi-exact fixed-decimal with specified precision and guard

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

from droop.common import UsageError

class Guarded(object):
    '''
    guarded-precision fixed-point decimal arithmetic 
    
    Note that because of approximate equality, Guarded numbers will not behave quite normally. 
    Equality is not transitive, and two "equal" values do not necessarily hash to the same value.
    
    This is acceptable for our purposes, but may not be generally desirable.
    '''
    
    name = 'guarded'
    info = None
    exact = True
    quasi_exact = True
    
    precision = None
    guard = None
    __scale = None
    __scalep = None
    __scaleg = None
    __dfmt = None     # display format

    @classmethod
    def helps(cls, helps):
        "add our help string"
        helps['guarded'] = '''Guarded arithmetic is an extension of fixed-point decimal arithmetic.
To its p digits of precision, it adds g guard digits. All arithmetic is done with p+g digits
of precision, but numbers that differ by less than half a unit of precision (10^g/2) are considered
to be equal.

If p & g are sufficiently large, guarded arithmetic produces the same outcomes as exact (rational)
arithmetic, but with considerably greater speed in most cases.

Options:
    precision=p   p digits of precision (default 9)
    guard=g       g guard digits (default p)

See also: fixed, rational
'''

    #  initialize must be called before using the class
    #
    @classmethod
    def initialize(cls, options=dict()):
        "initialize class variables"
        
        arithmetic = options.get('arithmetic', 'guarded')
        if arithmetic not in ('guarded', 'guarded'):
            raise UsageError('Guarded: unrecognized arithmetic type (%s)' % arithmetic)
            
        precision = options.get('precision', None) or 9
        try:
            cls.precision = int(precision)
        except ValueError:
            raise UsageError('Guarded: precision=%s; must be an int >= 0' % precision)
        if cls.precision < 0 or str(cls.precision) != str(precision):
            raise UsageError('Guarded: precision=%s; must be an int >= 0' % precision)
        guard = options.get('guard', None)
        if guard is None: guard = cls.precision
        try:
            cls.guard = int(guard)
        except ValueError:
            raise UsageError('Guarded: guard=%s; must be an int > 0' % guard)
        if cls.guard < 1 or str(cls.guard) != str(guard):
            raise UsageError('Guarded: guard=%s; must be an int > 0' % guard)

        cls.__scalep = 10 ** cls.precision
        cls.__scaleg = 10 ** cls.guard
        cls.__scale = 10 ** (cls.precision+cls.guard)
        
        #  __grnd is the rounding value for string conversions
        #  __geps is used in the test for equality (see __cmp__ below)
        #
        #  In the current implementation, we have a fairly narrow definition of equality, 
        #  a factor of 10 below one unit of precision.
        #
        cls.__grnd = cls.__scaleg//2
        cls.__geps = cls.__scaleg//2

        #  We keep statistics on how close our comparisons come to epsilon
        #
        #  maxDiff: the largest absolute difference less than epsilon (__cmp__ == 0)
        #  minDiff: the smallest absolute difference greater than epsilon (__cmp__ != 0)
        cls.maxDiff = 0
        cls.minDiff = cls.__scale * 100

        cls.__dfmt = "%d.%0" + str(cls.precision) + "d" # %d.%0pd

        cls.info = "guarded-precision fixed-point decimal arithmetic (%s+%s places)" % (str(cls.precision), str(cls.guard))

    def __init__(self, arg, setval=False):
        "create a new Guarded object"
        if setval:
            self._value = arg                  # direct-set value
        elif isinstance(arg, (int,long)):
            self._value = arg * self.__scale  # scale incoming integers
        else:
            self._value = arg._value          # copy incoming Guarded
        
    #  arithmetic operations
    #
    def __add__(self, other):
        "self + other"
        v = Guarded(other)
        return Guarded(self._value + v._value, True)

    def __sub__(self, other):
        "subtract other from self"
        v = Guarded(other)
        return Guarded(self._value - v._value, True)
        
    def __neg__(self):
        "return negated self"
        return Guarded(-self._value, True)

    def __pos__(self):
        "return +self"
        return Guarded(self, True)

    def __nonzero__(self):
        "bool(self)"
        return self._value != 0

    def __abs__(self):
        "absolute value"
        return Guarded(abs(self._value), True)
        
    def __mul__(self, other):
        "return self * other"
        if isinstance(other, (int,long)):
            return Guarded(self._value * other, True)
        return Guarded((self._value*other._value)//self.__scale, True)
        
    def __floordiv__(self, other):
        "return self // other"
        if isinstance(other, (int,long)):
            return Guarded(self._value // other, True)
        return Guarded((self._value * self.__scale) // other._value, True)

    __div__ = __floordiv__
    __truediv__ = __floordiv__

    #  we can't have hash because a == b doesn't imply identical hashes
    def __hash__(self):
        raise NotImplementedError

    @classmethod
    def mul(cls, arg1, arg2, round=None):
        '''
        return arg1 * arg2
        round is ignored   
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        v1._value = (v1._value * v2._value) // cls.__scale
        return v1
        
    @classmethod
    def div(cls, arg1, arg2, round=None):
        '''
        return arg1 / arg2
        round is ignored
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        v1._value = (v1._value * cls.__scale) // v2._value
        return v1

    @classmethod
    def muldiv(cls, arg1, arg2, arg3, round=None):
        '''
        return (arg1*arg2)/arg3
        
        a*b/c retains the full precision of a*b.
        round is ignored
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        v3 = cls(arg3)
        v1._value = (v1._value * v2._value) // v3._value
        return v1

    #  comparison operators
    #
    def __cmp__(self, other):
        gdiff = abs(self._value - other._value)
        if gdiff < self.__geps and gdiff > self.maxDiff:
            self.maxDiff = gdiff
        if gdiff >= self.__geps and gdiff < self.minDiff:
            self.minDiff = gdiff
        if gdiff < self.__geps:
            return 0
        if self._value > other._value:
            return 1
        return -1

    def __eq__(self, other):
        return self.__cmp__(other) == 0
    def __ne__(self, other):
        return self.__cmp__(other) != 0
    def __lt__(self, other):
        return self.__cmp__(other) < 0
    def __le__(self, other):
        return self.__cmp__(other) <= 0
    def __gt__(self, other):
        return self.__cmp__(other) > 0
    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    @classmethod
    def equal_within(cls, a, b, e):
        "test for equality within specified epsilon"
        return abs(a-b) < e
        
    @classmethod
    def min(cls, vals):
        "find actual minimum value in a list"
        min_ = vals[0]
        for val in vals[1:]:
            if val._value < min_._value:
                min_ = val
        return min_
 
    def __str__(self):
        '''
        stringify a guarded value
        print as full precision
        '''
        
        v = self._value
        gv = (v + self.__grnd) // self.__scaleg
        return Guarded.__dfmt % (gv // self.__scalep, gv % self.__scalep)

    @classmethod
    def report(cls):
        "Report arithmetic statistics"

        return """\
\tmaxDiff: %d  (s/b << geps)
\tgeps:    %d
\tminDiff: %d  (s/b >> geps)
\tguard:   %d
\tprec:    %d

""" % (
      cls.maxDiff,
      cls.__geps,
      cls.minDiff,
      cls.__scaleg,
      cls.__scale
      )
