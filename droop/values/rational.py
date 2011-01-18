'''
Rational value class
   Rational is essentially Fraction with support code

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

from fractions import Fraction

class Rational(Fraction):
    '''
    rational arithmetic with support functions
    
    '''
    name = 'rational'
    info = 'rational arithmetic'
    exact = True             # clients that care about such things can look at V.exact
    quasi_exact = False      # and V.quasi_exact to change their behavior
    dp = None    # str() display precision
    _dps = None  # display scale factor
    _dpr = None  # display rounding constant
    _dfmt = None # display format string
    __default_denominator = None    # earlier versions of Fraction require 1 rather than None
    
    @classmethod
    def tag(cls):
        "return a tag for unit test"
        return 'rational-d%d' % (cls.dp)

    @classmethod
    def helps(cls, helps):
        "add help string"
        helps['rational'] = '''Rational arithmetic uses rational fractions to exactly represent numeric values.

Options:
    display=d   display precision
                for display purposes only, round values to p digits of precision (default 12)

See also: fixed, guarded
'''

    @classmethod
    def initialize(cls, options):
        '''
        initialize class Rational, a value class based on Fraction
        
        options:
            display is the display precision (fixed-decimal with dp places); defaults to 12
        '''

        #  initialize __str__ parameters
        #
        if options.getopt('display') is None:              # don't override default set by rule
            options.setopt('display', default=12)
        cls.dp = options.getopt('display')                 # display precision
        cls._dps = 10 ** cls.dp                            # display scaler
        cls._dpr = Fraction(1, cls._dps*2)                 # display rounder
        cls._dfmt = "%d.%0" + str(cls.dp) + "d" # %d.%0_d  # display format
        #
        #  later versions of Fraction have a default denominator of None rather than 1,
        #  and more flexible conversion rules. However, earlier versions raise TypeError
        #  when called with denominator=None. Here we detect that condition and set the
        #  appropriate default.
        #
        try:
            Fraction(1, None)
        except TypeError:
            cls.__default_denominator = 1

    @classmethod
    def min(cls, vals):
        "find minimum value in a list"
        return min(vals)

    def __new__(cls, numerator=0, denominator=None):
        "create a new Rational object"
        if denominator is None:
            denominator = cls.__default_denominator
        self = Fraction.__new__(cls, numerator, denominator)
        return self

    def __str__(self):
        "represent Rational as fixed-decimal string"
        if self._numerator == 0 or self._denominator == 1:  # pylint: disable=E1101
            v = self._numerator * Rational._dps             # pylint: disable=E1101
        else:
            self += Rational._dpr  # add 1/2 of lsd for rounding
            v = self._numerator * Rational._dps / self._denominator
        return Rational._dfmt % (v // Rational._dps, v % Rational._dps)
    
    def __repr__(self): # pragma: no cover
        """repr(self)"""
        return ('Rational(%s, %s)' % (self._numerator, self._denominator))  # pylint: disable=E1101

    def __copy__(self): # pragma: no cover
        "borrowed from Fraction"
        if type(self) == Rational:
            return self     # I'm immutable; therefore I am my own clone
        return self.__class__(self._numerator, self._denominator)   # pylint: disable=E1101

    def __deepcopy__(self, memo):   # pragma: no cover
        "borrowed from Fraction"
        if type(self) == Rational:
            return self     # My components are also immutable
        return self.__class__(self._numerator, self._denominator)   # pylint: disable=E1101

    @staticmethod
    def report():
        "Report Rational arithmetic statistics"
        return ''  # nothing to report

    #  provide mul, div, muldiv for compatibility with non-exact arithmetic
    #
    @staticmethod
    def mul(arg1, arg2, round=None):   # pylint: disable=W0613,W0622
        '''
        return arg1 * arg2
        round is ignored       
        '''
        return Rational.__mul__(arg1, arg2)
        
    @staticmethod
    def div(arg1, arg2, round=None):   # pylint: disable=W0613,W0622
        '''
        return arg1 / arg2
        round is ignored
        '''
        return Rational.__div__(arg1, arg2)

    @staticmethod
    def muldiv(arg1, arg2, arg3, round=None):   # pylint: disable=W0613,W0622
        '''
        return (arg1*arg2)/arg3
        round is ignored
        '''
        return Rational.__div__(Rational.__mul__(arg1, arg2), arg3)

# create wrappers for Rational methods that return Rational (not Fraction) objects
#
def _wrap_method(method):
    "wrap a Fraction method in Rational"
    fraction_method = getattr(Fraction, method)
    def x(*args):
        "call Fraction method and change result to Rational"
        return Rational(fraction_method(*args))
    x.func_name = method    # pylint: disable=W0612
    setattr(Rational, method, x)

for name in "pos neg abs trunc".split():
    _wrap_method("__%s__" % name)   # wrap method, eg __pos__

for name in "add sub mul div truediv floordiv mod pow".split():
    _wrap_method("__%s__" % name)   # wrap method, eg __add__
    _wrap_method("__r%s__" % name)  # wrap reversed-argument method, eg __radd__

del _wrap_method