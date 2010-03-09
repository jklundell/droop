'''
Integer arithmetic
'''
import value

class Value(value.Value):
    "a Value class that implements integer"

    exact = False

    @classmethod
    def info(cls):
        "return description of arithmetic method"
        return "integer arithmetic"
        
    def __init__(self, arg):
        "create a new integer.Value object"
        if isinstance(arg, str) and arg == 'epsilon':
            self._value = 1
        elif isinstance(arg, (int,long)):
            self._value = int(arg)
        else:
            self._value = arg._value

    #  multiply & divide with rounding
    #
    def __mul__(self, other):
        '''
        return self * other
        '''
        if isinstance(other, (int,long)):
            v = Value(self)
            v._value *= other
            return v
        v = Value(other)
        v._value *= self._value
        return v
        
    def __floordiv__(self, other):
        '''
        return self // other
        '''
        v = Value(other)
        v._value, rem = divmod(self._value, v._value)
        return v

    __div__ = __floordiv__
    __truediv__ = __floordiv__
    
    #  multiply & divide with rounding
    #
    def _times_(self, other, round=None):
        '''
        return self * other
        round is ignored
        '''
        if isinstance(other, (int,long)):
            v = Value(self)
            v._value *= other
            return v
        v = Value(other)
        v._value *= self._value
        return v
        
    def _over_(self, other, round=None):
        '''
        return self // other
        round must be 'down' or 'up'
        
        Rounding down is simple truncation.
        Exact results are not rounded.
        '''
        if round not in ('down', 'up'):
            raise ValueError('integer.Value: must specify rounding: up or down')
        v = Value(other)
        v._value, rem = divmod(self._value, v._value)
        if rem and round == 'up':
            v._value += 1
        return v

    def _times_over_(self, mul, div, round=None):
        '''
        return (self*mul)//div, rounding final result
        
        a*b//c retains the full precision of a*b.
        Rules that require rounding of a*b must call
        _times_ and then _over_ separately.
        '''
        if round not in ('down', 'up'):
            raise ValueError('integer.Value: must specify rounding: up or down')
        v = Value(mul)
        d = Value(div)
        v._value *= self._value
        v._value, rem = divmod(v._value, d._value)
        if rem and round == 'up':
            v._value += 1
        return v
