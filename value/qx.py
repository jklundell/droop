'''
Quasi-exact fixed-point decimal arithmetic

If guard > 0, then QX will use quasi-exact guarded-precision arithmetic
See the appendix of http://www.votingmatters.org.uk/ISSUE24/I24P2.pdf
    for a brief description of quasi-exact arithmetic

maxDiff & minDiff are maintained to help determine whether the guard is sufficiently large

Values are stored internally as scaled integers, where the scale factor is 10^(precision+guard).

At some point, we might replace Value with an arithmetic
class that overloads its operators, but for now it seems
useful (and more transparent) to make the interface explicit.
'''

import value

class Value(value.Value):
    "a Value class that implements quasi-exact decimal fixed point"

    __scale = None
    __scalep = None
    __scaleg = None
    exact = True

    def __init__(self, arg):
        "create a new qx.Value object"
        self._value = Value.__fix(arg)

    @classmethod
    def __fix(cls, arg):
        "return scaled int of value without creating an object"
        if cls.__scale is None:
            raise TypeError('qx.Value must be initialized')
        if isinstance(arg, (int,long)):
            return arg * cls.__scale
        if isinstance(arg, cls):
            return arg._value
        raise TypeError("qx.Value can't convert %s" % type(arg))

    @classmethod
    def info(cls):
        "return description of arithmetic method"
        return "quasi-exact fixed-point decimal arithmetic; precision+guard: %d+%d digits" % (cls.__precision, cls.__guard)
        
    #  Value.init(precision) must be called before using the class
    #
    @classmethod
    def init(cls, precision, guard=None):
        "initialize class variables"
        if int(precision) != precision:
            raise ValueError('qx.Value: precision must be an int')
        if guard is None:
            guard = precision
        if int(guard) != guard:
            raise ValueError('qx.Value: guard must be an int')
        cls.__precision = precision
        cls.__guard = guard
        cls.__scalep = 10 ** precision
        cls.__scaleg = 10 ** guard
        cls.__scale = 10 ** (precision+guard)
        cls.__grnd = cls.__scaleg//2
        cls.__geps = cls.__scaleg//10
        cls.maxDiff = 0
        cls.minDiff = cls.__scale * 100

    #  arithmetic operations
    #
    #  Note that these ops do not alter self,
    #  but rather return the result with no side effect.
    #
    def __mul__(self, other):
        '''
        return self * other
        '''
        v = Value(self)
        if isinstance(other, (int,long)):
            v._value *= other
            return v  # no scaling needed
        v._value *= other._value
        v._value //= self.__scale
        return v
        
    def __floordiv__(self, other):
        '''
        return self / other
        '''
        v = Value(self)
        if isinstance(other, (int,long)):
            v._value //= other
            return v
        v._value *= self.__scale
        v._value //= other._value
        return v

    __div__ = __floordiv__
    __truediv__ = __floordiv__
    
    def _times_(self, other, round=None):
        '''
        return self * other
        round is ignored        
        '''
        v = Value(self)
        if isinstance(other, (int,long)):
            v._value *= other
            return v  # no scaling needed
        v._value *= other._value
        v._value //= self.__scale
        return v
        
    def _over_(self, other, round=None):
        '''
        return self / other
        round is ignored
        '''
        v = Value(self)
        if isinstance(other, (int,long)):
            v._value //= other
            return v
        v._value *= self.__scale
        v._value //= other._value
        return v

    def _times_over_(self, mul, div, round=None):
        '''
        return (self*mul)/div
        
        a*b/c retains the full precision of a*b.
        round is ignored
        '''
        v = Value(mul)
        d = Value(div)
        v._value *= self._value  # self * mul
        v._value //= d._value    # (self * mul) // div
        return v

    #  comparison operators
    #
    def _eq_(self, other):
        "return self == other"
        if self.__guard == 0:
            return self._value == other._value

        gdiff = abs(self._value - other._value)
        if gdiff < self.__geps and gdiff > self.maxDiff:
            self.maxDiff = gdiff
        if gdiff >= self.__geps and gdiff < self.minDiff:
            self.minDiff = gdiff
        return gdiff < self.__geps
        
    def _ne_(self, other):
        "return self != other"
        return not self.__eq__(other)
        
    def _lt_(self, other):
        "return self < other"
        return self._value < other._value and (self.__guard == 0 or not self._eq_(other))

    def _gt_(self, other):
        "return self > other"
        return self._value > other._value and (self.__guard == 0 or not self._eq_(other))

    def _le_(self, other):
        "return self <= other"
        return not self._gt_(other)

    def _ge_(self, other):
        "return self >= other"
        return not self._lt_(other)

    #  comparison overloads
    #
    def __eq__(self, other):
        "return self == other"
        if self.__guard == 0:
            return self._value == other._value

        gdiff = abs(self._value - other._value)
        if gdiff < self.__geps and gdiff > self.maxDiff:
            self.maxDiff = gdiff
        if gdiff >= self.__geps and gdiff < self.minDiff:
            self.minDiff = gdiff
        return gdiff < self.__geps
        
    def __ne__(self, other):
        "return self != other"
        return not self.__eq__(other)
        
    def __lt__(self, other):
        "return self < other"
        return self._value < other._value and (self.__guard == 0 or not self.__eq__(other))

    def __gt__(self, other):
        "return self > other"
        return self._value > other._value and (self.__guard == 0 or not self.__eq__(other))

    def __le__(self, other):
        "return self <= other"
        return not self.__gt__(other)

    def __ge__(self, other):
        "return self >= other"
        return not self.__lt__(other)

    def __str__(self):
        '''
        stringify a quasi-exact value
        
        print as full precision
        '''
        if self.__precision == 0: # integer arithmetic
            return str(self._value)
        v = self._value
        s = Value.__scale
        if s == 1:
            return str(v)
        nfmt = "%d.%0" + str(Value.__precision) + "d" # %d.%0_d
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
