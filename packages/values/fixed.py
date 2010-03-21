'''
Fixed value class
   Fixed supports fixed-decimal arithmetic,
   including integer if precision is set to zero.

copyright 2010 by Jonathan Lundell
'''

class Fixed(object):
    '''
    fixed-point decimal arithmetic
    '''
    
    name = 'fixed'     # or 'integer'
    info = None
    exact = False
    quasi_exact = False
    epsilon = None     # smallest value > 0
    
    precision = None  # precision in decimal digits
    __scale = None      # scale factor
    __dfmt = None       # display format

    #  initialize must be called before using the class
    #
    @classmethod
    def initialize(cls, options=dict()):
        "initialize class variables"
        
        arithmetic = options.get('arithmetic', 'qx')
        if arithmetic not in ('fixed', 'integer'):
            raise TypeError('Fixed: unrecognized arithmetic type (%s)' % arithmetic)
        precision = options.get('precision', None) or 9
        if arithmetic == 'integer':
            precision = 0
        if precision == 0:
            cls.name = 'integer'
        if int(precision) != precision or precision < 0:
            raise TypeError('Fixed: precision must be an int >= 0')

        cls.precision = precision
        cls.__scale = 10 ** (precision)
        
        cls.epsilon = cls(0)
        cls.epsilon._value = 1

        cls.__dfmt = "%d.%0" + str(precision) + "d" # %d.%0pd

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
    def equal_within(cls, a, b, e):
        "test for equality within epsilon"
        return abs(a-b) < e
        
    def __str__(self):
        '''
        stringify a quasi-exact value
        print as full precision
        '''
        v = self._value
        if Fixed.precision == 0:  # integer arithmetic
            return str(v)
        return self.__dfmt % (v//self.__scale, v%self.__scale)

    @classmethod
    def report(cls):
        "Report arithmetic statistics"
        return ''  # nothing to report
