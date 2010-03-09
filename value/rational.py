'''
Rational arithmetic

Values are stored internally as fractions.Fraction
where the scale factor is 10^precision.
'''

import fractions
import value

class Value(value.Value):
    "a Value class that implements rationals"

    exact = True

    @classmethod
    def info(cls):
        "return description of arithmetic method"
        return "rational arithmetic"
        
    def __init__(self, arg):
        "create a new rational.Value object"
        if isinstance(arg, (int,long)):
            self._value = fractions.Fraction(arg)
        else:
            self._value = arg._value

    #  arithmetic operations
    #
    #  Note that these ops do not alter self,
    #  but rather return the result with no side effect.
    #
    def __mul__(self, other):
        "return self * other"
        v = Value(other)
        v._value *= self._value
        return v
        
    def __floordiv__(self, other):
        "return self / other"
        v = Value(other)
        v._value = self._value / v._value
        return v

    __div__ = __floordiv__
    __truediv__ = __floordiv__
    
    def _times_(self, other, round=None):
        '''
        return self * other
        round is ignored
        '''
        v = Value(other)
        v._value *= self._value
        return v
        
    def _over_(self, other, round=None):
        '''
        return self / other
        round is ignored
        '''
        v = Value(other)
        v._value = self._value / v._value
        return v

    def _times_over_(self, mul, div, round=None):
        '''
        return (self*mul)/div
        round is ignored
        '''
        v1 = Value(mul)
        v2 = Value(div)
        v1._value = self._value * v1._value / v2._value
        return v1
