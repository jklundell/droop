'''
Value classes
   Rational is essentially Fraction
   Fixed supports integer, fixed-decimal and quasi-exact fixed-decimal

copyright 2010 by Jonathan Lundell
'''

class Value(object):
    "a Value class that implements rationals"

    @staticmethod
    def ArithmeticClass(options=dict()):
        "initialize a value class and return it"

        arithmetic = options.get('arithmetic', None) or 'quasi-exact'
        if arithmetic == 'rational':
            Rational.initialize(options)
            return Rational
        if arithmetic in ('fixed', 'quasi-exact', 'qx', 'integer'):
            Fixed.initialize(options)
            return Fixed

#  TODO (maybe)
#  wrap the entire Fraction class in Rational per Patrick Maupin's idea:
#  http://groups.google.com/group/comp.lang.python/browse_frm/thread/1253bbab7dfd4b/59289c16603fb374?hl=en&lnk=gst&q=pmaupin+userint#59289c16603fb374
#
# print """ 
# \"""A more or less complete user-defined wrapper around integer objects.\""" 
# class UserInt(object): 
#     def __int__(self):  raise TypeError, "This is a virtual class" 
# """ 
# unwanted_methods = dir(object)+['__int__','__getnewargs__'] 
# methods = [i for i in dir(int) if i not in unwanted_methods] 
# methods.sort() 
# for i in methods: 
#     try: getattr(1,i)(1) 
#     except TypeError: params = (i,'',i,'') 
#     else: params = (i,',other',i,'int(other)') 
#     print '    def %s(self%s): return int(self).%s(%s)' % params 

from fractions import Fraction

class Rational(Fraction):
    '''
    rational arithmetic with support functions and approximate equality
    
    Note that because of approximate equality, Rational numbers will not behave
    quite normally. Equality is not transitive, and two "equal" Rationals do not 
    necessarily hash to the same value.
    
    This is acceptable for our purposes, but may not be generally desirable.
    '''
    
    exact = True
    epsilon = None
    name = 'rational'
    info = 'rational arithmetic'
    
    @classmethod
    def initialize(cls, options=dict()):
        '''
        initialize class Rational, a value class based on Fraction
        
        options:
            epsilon (default 10) sets the value used to determine equality to 1/10^epsilon
            
            a == b is defined as abs(a - b) < 1/10**epsilon
        '''
        epsilon = options.get('epsilon', None) or 10
        cls.epsilon = Fraction(1,10**epsilon)
        cls.info = 'rational arithmetic (epsilon=%d)' % epsilon

    #  define equality as approximate equality,
    #  and define other relationships consistently
    #
    def __cmp__(self, other):
        if abs(Fraction.__sub__(self, other)) < self.epsilon:
            return 0
        if Fraction.__gt__(self, other):
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
    def __ge__(self, other):
        return self.__cmp__(other) >= 0
    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __nonzero__(self):
        return abs(self) >= self.epsilon  # consistent with self == 0

    def __add__(self, other):
        return Rational(Fraction.__add__(self, other))
    def __sub__(self, other):
        return Rational(Fraction.__sub__(self, other))
    def __rsub__(self, other):
        return Rational(Fraction.__rsub__(self, other))
    def __mul__(self, other):
        return Rational(Fraction.__mul__(self, other))
    def __div__(self, other):
        return Rational(Fraction.__div__(self, other))
    def __rdiv__(self, other):
        return Rational(Fraction.__rdiv__(self, other))
    def __neg__(self):
        return Rational(Fraction.__neg__(self))
    def __pos__(self):
        return self
    __radd__ = __add__
    __rmul__ = __mul__
    __floordiv__ = __div__
    __truediv__ = __div__

    #  we can't have hash because a == b doesn't imply identical hashes
    def __hash__(self):
        raise NotImplementedError
    
    @staticmethod
    def report():
        "Report arithmetic statistics"
        return ''

    #  provide mul, div, muldiv for compatibility with non-exact arithmetic
    #
    @staticmethod
    def mul(arg1, arg2, round=None):
        '''
        return arg1 * arg2
        round is ignored       
        '''
        return Rational(arg1) * Rational(arg2)
        
    @staticmethod
    def div(arg1, arg2, round=None):
        '''
        return arg1 / arg2
        round is ignored
        '''
        return Rational(arg1) / Rational(arg2)

    @staticmethod
    def muldiv(arg1, arg2, arg3, round=None):
        '''
        return (arg1*arg2)/arg3
        round is ignored
        '''
        return Rational(arg1) * Rational(arg2) / Rational(arg3)

class Fixed(object):
    '''
    fixed-point decimal arithmetic with optional guard digits
    
    Note that because of approximate equality, Fixed quasi-exact (ie, guard>0) numbers 
    will not behave quite normally. Equality is not transitive, and two "equal" valules
    do not necessarily hash to the same value.
    
    This is acceptable for our purposes, but may not be generally desirable.
    '''
    
    __scale = None
    __scalep = None
    __scaleg = None
    epsilon = None
    name = None
    info = None

    #  Fixed.init(precision) must be called before using the class
    #
    @classmethod
    def initialize(cls, options=dict()):
        "initialize class variables"
        
        arithmetic = options.get('arithmetic', 'qx')
        if arithmetic not in ('fixed', 'quasi-exact', 'qx', 'integer'):
            raise TypeError('unrecognized arithmetic type (%s)' % arithmetic)
        if arithmetic == 'integer':
            cls.name = 'integer'
            precision = 0
            guard = None
        else:
            precision = options.get('precision', None) or 9
            if int(precision) != precision or precision < 0:
                raise TypeError('value.Fixed: precision must be an int >= 0')
            if arithmetic == 'fixed':
                cls.name = 'fixed'
                guard = 0
            else:
                cls.name = 'quasi-exact'
                guard = options.get('guard', None)
                if guard is None: guard = precision
                if int(guard) != guard or guard <= 0:
                    raise TypeError('value.Fixed: quasi-exact guard must be an int > 0')

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
        cls.epsilon = cls(0)
        if not cls.exact:
            cls.epsilon._value = 1

        if arithmetic == 'integer':
            cls.info = "integer arithmetic"
        elif arithmetic == 'fixed':
            cls.info = "fixed-point decimal arithmetic (%s places)" % str(cls.__precision)
        else:
            cls.info = "quasi-exact fixed-point decimal arithmetic (%s+%s places)" % (str(cls.__precision), str(cls.__guard))

    def __init__(self, arg):
        "create a new Fixed object"
        self._value = Fixed.__fix(arg)
        
    @classmethod
    def __fix(cls, arg):
        "return scaled int of value without creating an object"
        if isinstance(arg, (int,long)):
            return arg * cls.__scale
        return arg._value

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

    #  we can't have hash because a == b doesn't imply identical hashes
    def __hash__(self):
        raise NotImplementedError

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
            v1._value = (v1._value * Fixed.__scale) // v2._value
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
        v1._value, rem = divmod(v1._value * v2._value, v3._value)
        if not Fixed.exact:
            if round not in ('down', 'up'):
                raise ValueError('Fixed.muldiv: must specify rounding: up or down')
            if rem and round == 'up':
                v1._value += 1
        return v1

    #  comparison operators
    #
    def __cmp__(self, other):
        if not Fixed.exact:
            return self._value.__cmp__(other._value)
        gdiff = abs(self._value - other._value)
        if gdiff < Fixed.__geps and gdiff > Fixed.maxDiff:
            Fixed.maxDiff = gdiff
        if gdiff >= Fixed.__geps and gdiff < Fixed.minDiff:
            Fixed.minDiff = gdiff
        if gdiff < Fixed.__geps:
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

    def __str__(self):
        '''
        stringify a quasi-exact value
        print as full precision
        '''
        v = self._value
        if not self.__guard:       # fixed-point decimal arithmetic
            if Fixed.__scale == 1:  # integer arithmetic
                return str(v)
            nfmt = "%d.%0" + str(Fixed.__precision) + "d" # %d.%0_d
            return nfmt % (v//Fixed.__scale, v%Fixed.__scale)
        nfmt = "%d.%0" + str(Fixed.__precision) + "d" # %d.%0_d
        gv = (v + self.__grnd)//self.__scaleg
        return nfmt % (gv//self.__scalep, gv%self.__scalep)

    @staticmethod
    def report():
        "Report arithmetic statistics"

        if not Fixed.__guard:
            return ''
        s = """\
\tmaxDiff: %d  (s/b << geps)
\tgeps:    %d
\tminDiff: %d  (s/b >> geps)
\tguard:   %d
\tprec:    %d

""" % (
      Fixed.maxDiff,
      Fixed.__geps,
      Fixed.minDiff,
      Fixed.__scaleg,
      Fixed.__scale
      )
        return s
