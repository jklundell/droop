'''
Rational value class
   Rational is essentially Fraction with support code

copyright 2010 by Jonathan Lundell
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
    
    @classmethod
    def help(cls, subject):
        "return help on this arithmetic class"
        return 'rational'

    @classmethod
    def initialize(cls, options=dict()):
        '''
        initialize class Rational, a value class based on Fraction
        
        options:
            dp is the display precision (fixed-decimal with dp places); defaults to 10
        '''

        #  initialize __str__ parameters
        #
        cls.dp = options.get('dp', None) or 12             # display precision
        cls._dps = 10 ** cls.dp                            # display scaler
        cls._dpr = Fraction(1, cls._dps*2)                 # display rounder
        cls._dfmt = "%d.%0" + str(cls.dp) + "d" # %d.%0_d  # display format

    @staticmethod
    def equal_within(a, b, e):
        "test for equality within specified epsilon"
        return abs(a-b) < e

    #  leave repr alone, but redefine str as decimal notation for readability
    def __str__(self):
        "represent Rational as fixed-decimal string"
        self += Rational._dpr  # add 1/2 of lsd for rounding
        if self._numerator == 0 or self._denominator == 1:
            v = self._numerator * Rational._dps
        else:
            v = self._numerator * Rational._dps / self._denominator
        return Rational._dfmt % (v//Rational._dps, v%Rational._dps)
    
    @staticmethod
    def report():
        "Report Rational arithmetic statistics"
        return ''  # nothing to report

    #  provide mul, div, muldiv for compatibility with non-exact arithmetic
    #
    @staticmethod
    def mul(arg1, arg2, round=None):
        '''
        return arg1 * arg2
        round is ignored       
        '''
        return Fraction.__mul__(arg1, arg2)
        
    @staticmethod
    def div(arg1, arg2, round=None):
        '''
        return arg1 / arg2
        round is ignored
        '''
        return Fraction.__div(arg1, arg2)

    @staticmethod
    def muldiv(arg1, arg2, arg3, round=None):
        '''
        return (arg1*arg2)/arg3
        round is ignored
        '''
        return Fraction.__div__(Fraction.__mul__(arg1, arg2), arg3)

