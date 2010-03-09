'''
Abstract base for other Value classes

'''

class Value(object):
    "a Value class that implements rationals"

    @staticmethod
    def ArithmeticClass(arithmetic, precision=None, guard=None):
        "initialize a value class and return it"
        #
        #  temporary shim for old interface
        #
        if arithmetic == 'rational':
            precision = guard = None
        if arithmetic == 'integer':
            arithmetic = 'fixed'
            precision = guard = 0
        elif arithmetic == 'fixed':
            guard = 0
        elif arithmetic == 'qx':
            arithmetic = 'fixed'
        #   end shim
        
        if precision is None:
            return Rational
        if guard is None:
            guard = precision
        Fixed.init(precision, guard)
        return Fixed

import fractions

class Rational(fractions.Fraction):
    "rational arithmetic with support functions"
    
    exact = True
    
    @classmethod
    def info(cls):
        return 'rational arithmetic'


class Fixed(object):
    "fixed-point decimal arithmetic with optional guard digits"
    
    __scale = None
    __scalep = None
    __scaleg = None

    def __init__(self, arg):
        "create a new Fixed object"
        if isinstance(arg, str) and arg == 'epsilon':
            if Fixed.exact:
                raise ValueError('exact arithmetic has no epsilon')
            self._value = 1
        else:
            self._value = Fixed.__fix(arg)

    @classmethod
    def __fix(cls, arg):
        "return scaled int of value without creating an object"
        if cls.__scale is None:
            raise TypeError('value.Fixed must be initialized')
        if isinstance(arg, (int,long)):
            return arg * cls.__scale
        if isinstance(arg, cls):
            return arg._value
        raise TypeError("value.Fixed can't convert %s" % type(arg))

    @classmethod
    def info(cls):
        "return description of arithmetic method"
        if not cls.__precision:
            return "integer arithmetic"
        if not cls.__guard:
            return "fixed-point decimal arithmetic (%s places)" % str(cls.__precision)
        return "quasi-exact fixed-point decimal arithmetic (%s+%s places)" % (str(cls.__precision), str(cls.__guard))
        
    #  Fixed.init(precision) must be called before using the class
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
            raise ValueError('Fixed.mul: must specify rounding: up or down')
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
            raise ValueError('Fixed.div: must specify rounding: up or down')
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
            raise ValueError('Fixed.muldiv: must specify rounding: up or down')


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
        '''
        stringify a quasi-exact value
        print as full precision
        '''
        v = self._value
        if self.__guard == 0:       # fixed-point decimal arithmetic
            if Fixed.__scale == 1:  # integer arithmetic
                return str(v)
            nfmt = "%d.%0" + str(Fixed.__precision) + "d" # %d.%0_d
            return nfmt % (v//Fixed.__scale, v%Fixed.__scale)
        nfmt = "%d.%0" + str(Fixed.__precision) + "d" # %d.%0_d
        gv = (v + self.__grnd)//self.__scaleg
        return nfmt % (gv//self.__scalep, gv%self.__scalep)

    def report(self):
        "Report qx statistics"

        s = """\
maxDiff: %d  (s/b << geps)
geps:    %d
minDiff: %d  (s/b >> geps)
guard:   %d
prec:    %d

""" % (
      self.maxDiff,
      self.__geps,
      self.minDiff,
      self.__scaleg,
      self.__scale
      )
        return s
