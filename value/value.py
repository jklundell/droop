'''
Abstract base for other Value classes

'''

class Value(object):
    "a Value class that implements rationals"

    exact = None
    NumberClass = None
    arithmetic = None
    precision = None
    guard = None

    @staticmethod
    def ArithmeticClass(arithmetic, precision=None, guard=None):
        "initialize a value class and return it"
        Value.arithmetic = arithmetic
        Value.precision = precision
        Value.guard = guard
        if arithmetic == 'rational':
            import fractions
            Value.NumberClass = fractions.Fraction
            Value.exact = True
        elif arithmetic == 'fixed':
            Value.NumberClass = Fixed
            Value.exact = bool(guard)
            Fixed.init(precision, guard)
        else:
            raise ValueError('unknown arithmetic %s' % arithmetic)
        return Value.NumberClass

    @classmethod
    def info(cls):
        "return description of arithmetic method"
        if cls.arithmetic == 'rational':
            return "rational arithmetic"
        if cls.arithmetic == 'fixed':
            if not cls.precision:
                return "integer arithmetic"
            if not cls.guard:
                return "fixed-point decimal arithmetic (%s places)" % str(cls.precision)
            return "quasi-exact fixed-point decimal arithmetic (%s+%s places)" % (str(cls.precision), str(cls.guard))
        return "unknown arithmetic (%s)" % cls.arithmetic
        
class Fixed(object):
    "fixed-point decimal arithmetic with optional guard digits"
    
    __scale = None
    __scalep = None
    __scaleg = None

    def __init__(self, arg):
        "create a new Fixed.Value object"
        self._value = Fixed.__fix(arg)

    def __fix(self, arg):
        "return scaled int of value without creating an object"
        if self.__scale is None:
            raise TypeError('value.Fixed must be initialized')
        if isinstance(arg, (int,long)):
            return arg * self.__scale
        if isinstance(arg, self):
            return arg._value
        raise TypeError("value.Fixed can't convert %s" % type(arg))

    #  Value.init(precision) must be called before using the class
    #
    @classmethod
    def init(cls, precision, guard=None):
        "initialize class variables"
        if int(precision) != precision:
            raise ValueError('value.Fixed: precision must be an int')
        if guard is None:
            guard = precision
        if int(guard) != guard:
            raise ValueError('value.Fixed: guard must be an int')
        cls.__precision = precision
        cls.__guard = guard
        cls.__scalep = 10 ** precision
        cls.__scaleg = 10 ** guard
        cls.__scale = 10 ** (precision+guard)
        cls.__grnd = cls.__scaleg//2
        cls.__geps = cls.__scaleg//10
        cls.maxDiff = 0
        cls.minDiff = cls.__scale * 100
        cls.exact = bool(guard)
        if not cls.exact:
            cls.epsilon = cls(1) // cls(cls.__scalep)

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

    def __mul__(self, other):
        "return self * other"
        v = Value(self)
        if isinstance(other, (int,long)):
            v._value *= other
            return v  # no scaling needed
        v._value *= other._value
        v._value //= self.__scale
        return v
        
    def __floordiv__(self, other):
        "return self // other"
        v = Value(self)
        if isinstance(other, (int,long)):
            v._value //= other
            return v
        v._value *= self.__scale
        v._value //= other._value
        return v

    __div__ = __floordiv__
    __truediv__ = __floordiv__
    
    @staticmethod
    def mul(arg1, arg2, round=None):
        '''
        return arg1 * arg2
        round is ignored if exact       
        '''
        v1 = Fixed(arg1)
        v2 = Fixed(arg2)
        if Fixed.exact:
            v1._value = (v1._value * v2._value) // Fixed.__scale
            return v1
        if round not in ('down', 'up'):
            raise ValueError('fixed.Value: must specify rounding: up or down')
        v1._value, rem = divmod(v1._value * v2._value, Fixed.__scale)
        if rem and round == 'up':
            v1._value += 1
        return v1
        
    @staticmethod
    def div(arg1, arg2, round=None):
        '''
        return arg1 / arg2
        round is ignored if exact
        '''
        v1 = Fixed(arg1)
        v2 = Fixed(arg2)
        if Fixed.exact:
            v1._value = (v1.__value * Fixed.__scale) // v2._value
            return v1
        if round not in ('down', 'up'):
            raise ValueError('fixed.Value: must specify rounding: up or down')
        v1._value, rem = divmod(v1._value * Fixed.__scale, v2._value)
        if rem and round == 'up':
            v1._value += 1
        return v1

    @staticmethod
    def muldiv(arg1, arg2, arg3, round=None):
        '''
        return (arg1*arg2)/arg3
        
        a*b/c retains the full precision of a*b.
        round is ignored if exact
        '''
        v1 = Fixed(arg1)
        v2 = Fixed(arg2)
        v3 = Fixed(arg3)
        if Fixed.exact:
            v1._value = (v1._value * v2._value) // v3._value
            return v1
        if round not in ('down', 'up'):
            raise ValueError('fixed.Value: must specify rounding: up or down')


    #  comparison operators
    #
    def __eq__(self, other):
        "return self == other"
        return self._value == other._value
    def __ne__(self, other):
        "return self != other"
        return self._value != other._value 
    def __lt__(self, other):
        "return self < other"
        return self._value < other._value
    def __le__(self, other):
        "return self <= other"
        return self._value <= other._value
    def __gt__(self, other):
        "return self > other"
        return self._value > other._value
    def __ge__(self, other):
        "return self >= other"
        return self._value >= other._value

    def __str__(self):
        "stringify a value"
        return str(self._value)
        
    def report(self):
        "hook for post-election reporting"
        return None
