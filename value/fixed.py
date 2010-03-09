'''
Fixed-point decimal arithmetic

Values are stored internally as scaled integers, 
where the scale factor is 10^precision.
'''
import value

class Value(value.Value):
    "a Value class that implements decimal fixed point"

    __scale = None
    exact = False

    def __init__(self, arg):
        "create a new fixed.Value object"
        if isinstance(arg, str) and arg == 'epsilon':
            self._value = 1
        else:
            self._value = Value.__fix(arg)

    @classmethod
    def __fix(cls, arg):
        "return scaled int of value without creating an object"
        if cls.__scale is None:
            raise TypeError('fixed.Value must be initialized')
        if isinstance(arg, (int,long)):
            return arg * cls.__scale
        if isinstance(arg, cls):
            return arg._value
        raise TypeError("fixed.Value can't convert %s" % type(arg))

    @classmethod
    def info(cls):
        "return description of arithmetic method"
        return "fixed-point decimal arithmetic; precision: %d digits" % cls.__precision
        
    #  Value.init(precision) must be called before using the class
    #
    @classmethod
    def init(cls, precision):
        "initialize class variables"
        if int(precision) != precision:
            raise ValueError('fixed.Value: precision must be an int')
        cls.__precision = precision
        cls.__scale = 10 ** precision
        cls.__rounder = 1

    #  arithmetic operations
    #
    def __mul__(self, other):
        '''
        return self * other
        rounds down
        
        If other is an int, the result is always exact.
        
        Rounding down is simple truncation.
        Exact results are not rounded.
        
        '''
        if isinstance(other, (int,long)):
            v = Value(self)
            v._value *= other
            return v
        v = Value(other)
        v._value = (self._value * v._value) // Value.__scale
        return v
        
    def __floordiv__(self, other):
        '''
        return self // other
        rounds down
        
        Rounding down is simple truncation.
        Exact results are not rounded.
        '''
        v = Value(other)
        v._value = (self._value * Value.__scale) // v._value
        return v

    __div__ = __floordiv__
    __truediv__ = __floordiv__
    
    #  multiplication & division with rounding
    #
    def _times_(self, other, round=None):
        '''
        return self * other
        round must be 'down' or 'up'
        
        If other is an int, the result is always exact,
        so we don't test round and don't convert other.
        Otherwise we require that round is specified explicitly.
        
        Rounding down is simple truncation.
        Exact results are not rounded.
        
        '''
        if isinstance(other, (int,long)):
            v = Value(self)
            v._value *= other
            return v  # no rounding needed
        if round not in ('down', 'up'):
            raise ValueError('fixed.Value: must specify rounding: up or down')
        v = Value(other)
        v._value, rem = divmod(self._value * v._value, Value.__scale)
        if rem and round == 'up':
            v._value += Value.__rounder
        return v
        
    def _over_(self, other, round=None):
        '''
        return self // other
        round must be 'down' or 'up'
        
        Rounding down is simple truncation.
        Exact results are not rounded.
        '''
        if round not in ('down', 'up'):
            raise ValueError('fixed.Value: must specify rounding: up or down')
        v = Value(other)
        v._value, rem = divmod(self._value * Value.__scale, v._value)
        if rem and round == 'up':
            v._value += Value.__rounder
        return v

    def _times_over_(self, mul, div, round=None):
        '''
        return (self*mul)//div, rounding final result
        
        a*b//c retains the full precision of a*b.
        Rules that require rounding of a*b must call
        _times_ and then _over_ separately.
        '''
        if round not in ('down', 'up'):
            raise ValueError('fixed.Value: must specify rounding: up or down')
        v = Value(mul)
        d = Value(div)
        v._value *= self._value # retain full precision
        v._value, rem = divmod(v._value, d._value)
        if rem and round == 'up':
            v._value += Value.__rounder
        return v

    def __str__(self):
        '''
        stringify a value
        
        print as full precision
        '''
        v = self._value
        s = Value.__scale
        if s == 1:
            return str(v)
        nfmt = "%d.%0" + str(Value.__precision) + "d" # %d.%0_d
        return nfmt % (v//s, v%s)
