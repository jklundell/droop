'''
Fixed value class
   Fixed supports fixed-decimal arithmetic,
   including integer if precision is set to zero.

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

class Fixed(object):
    '''
    fixed-point decimal arithmetic
    '''
    __slots__ = '_value'
    name = 'fixed'      # or 'integer'
    info = None
    exact = False
    quasi_exact = False
    epsilon = None      # smallest value > 0
    
    precision = None    # precision in decimal digits
    display = None      # display precision, in decimal digits
    __scale = None      # scale factor
    __dfmt = None       # display format
    __scaled = None     # display scale factor
    
    @classmethod
    def tag(cls):
        "return a tag for unit test"
        if cls.precision == 0:
            return 'integer'
        return 'fixed-p%d-d%d' % (cls.precision, cls.display)

    @classmethod
    def helps(cls, helps):
        "add help string"
        helps['fixed'] = '''Fixed arithmetic uses fixed-point decimal arithmetic with a specified
number of digits of precision.

Options:
    precision=p   p digits of precision (default 9)
    precision=0   integer arithmetic

See also: guarded, rational
'''

    #  initialize must be called before using the class
    #
    @classmethod
    def initialize(cls, options=dict()):
        "initialize class variables"
        
        arithmetic = options.get('arithmetic', 'qx')
        if arithmetic not in ('fixed', 'integer'):
            raise UsageError('Fixed: unrecognized arithmetic type (%s)' % arithmetic)
        precision = options.get('precision', None) or 9
        if arithmetic == 'integer':
            precision = 0
        if precision == 0:
            cls.name = 'integer'
        try:
            cls.precision = int(precision)
        except ValueError:
            raise UsageError('Guarded: precision=%s; must be an int >= 0' % precision)
        if cls.precision < 0 or str(cls.precision) != str(precision):
            raise UsageError('Guarded: precision=%s; must be an int >= 0' % precision)

        cls.__scale = 10 ** cls.precision
        cls.display = cls.precision
        cls.__scaled = 10 ** cls.display
        
        cls.epsilon = cls(0)
        cls.epsilon._value = 1

        cls.__dfmt = "%d.%0" + str(cls.precision) + "d" # %d.%0pd

        if cls.name == 'integer':
            cls.info = "integer arithmetic"
        else:
            cls.info = "fixed-point decimal arithmetic (%s places)" % str(cls.precision)

    def __init__(self, arg):
        "create a new Fixed object"
        if isinstance(arg, (int,long)):
            self._value = arg * self.__scale  # scale incoming integers
        else:
            self._value = arg._value          # copy incoming Fixed
        
    #  arithmetic operations
    #
    def __add__(self, other):
        "self + other"
        v = Fixed(other)
        v._value += self._value
        return v

    def __sub__(self, other):
        "subtract other from self"
        v = Fixed(other)
        v._value = self._value - v._value
        return v
        
    def __neg__(self):
        "return negated self"
        v = Fixed(self)
        v._value = -v._value
        return v

    def __pos__(self):
        "return +self"
        return Fixed(self)

    def __nonzero__(self):
        "bool(self)"
        return self._value != 0

    def __abs__(self):
        "absolute value"
        return Fixed(abs(self._value))
        
    def __mul__(self, other):
        "return self * other"
        v = Fixed(self)
        if isinstance(other, (int,long)):
            v._value *= other
            return v  # no scaling needed
        v._value *= other._value
        v._value //= self.__scale
        return v
        
    def __floordiv__(self, other):
        "return self // other"
        v = Fixed(self)
        if isinstance(other, (int,long)):
            v._value //= other
            return v
        v._value *= self.__scale
        v._value //= other._value
        return v

    __div__ = __floordiv__
    __truediv__ = __floordiv__

    @classmethod
    def mul(cls, arg1, arg2, round=None):
        '''
        return arg1 * arg2
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        if round not in ('down', 'up'):
            raise ValueError('Fixed.mul: must specify rounding: up or down')
        v1._value, rem = divmod(v1._value * v2._value, cls.__scale)
        if rem and round == 'up':
            v1._value += 1
        return v1
        
    @classmethod
    def div(cls, arg1, arg2, round=None):
        '''
        return arg1 / arg2
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        if round not in ('down', 'up'):
            raise ValueError('Fixed.div: must specify rounding: up or down')
        v1._value, rem = divmod(v1._value * cls.__scale, v2._value)
        if rem and round == 'up':
            v1._value += 1
        return v1

    @classmethod
    def muldiv(cls, arg1, arg2, arg3, round=None):
        '''
        return (arg1*arg2)/arg3
        
        a*b/c retains the full precision of a*b.
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        v3 = cls(arg3)
        v1._value, rem = divmod(v1._value * v2._value, v3._value)
        if round not in ('down', 'up'):
            raise ValueError('Fixed.muldiv: must specify rounding: up or down')
        if rem and round == 'up':
            v1._value += 1
        return v1

    #  comparison operators
    #
    def __cmp__(self, other):
        return long(self._value).__cmp__(long(other._value))

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
    def min(cls, vals):
        "find minimum value in a list"
        return min(vals)
 
    def __str__(self):
        '''
        stringify a fixed value
        print as full precision
        '''
        v = self._value
        if Fixed.precision == 0:  # integer arithmetic
            return str(v)
        return self.__dfmt % (v//self.__scaled, v%self.__scaled)

    @classmethod
    def report(cls):
        "Report arithmetic statistics"
        return ''  # nothing to report
