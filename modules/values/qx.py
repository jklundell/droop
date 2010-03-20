'''
Quasi-exact value class
   QX supports quasi-exact fixed-decimal with specified precision and guard

copyright 2010 by Jonathan Lundell
'''

class QX(object):
    '''
    quasi-exact fixed-point decimal arithmetic with guard digits
    
    Note that because of approximate equality, Fixed quasi-exact (ie, guard>0) numbers 
    will not behave quite normally. Equality is not transitive, and two "equal" valules
    do not necessarily hash to the same value.
    
    This is acceptable for our purposes, but may not be generally desirable.
    '''
    
    name = 'quasi-exact'
    info = None
    exact = True
    quasi_exact = True
    
    precision = None
    guard = None
    __scale = None
    __scalep = None
    __scaleg = None
    __dfmt = None     # display format

    #  initialize must be called before using the class
    #
    @classmethod
    def initialize(cls, options=dict()):
        "initialize class variables"
        
        arithmetic = options.get('arithmetic', 'qx')
        if arithmetic not in ('quasi-exact', 'qx'):
            raise TypeError('QX: unrecognized arithmetic type (%s)' % arithmetic)
            
        precision = options.get('precision', None) or 9
        if int(precision) != precision or precision < 0:
            raise TypeError('QX: precision must be an int >= 0')
        guard = options.get('guard', None)
        if guard is None: guard = precision
        if int(guard) != guard or guard < 1:
            raise TypeError('QX: guard must be an int > 0')

        cls.precision = precision
        cls.guard = guard

        cls.__scalep = 10 ** precision
        cls.__scaleg = 10 ** guard
        cls.__scale = 10 ** (precision+guard)
        cls.__grnd = cls.__scaleg//2
        cls.__geps = cls.__scaleg//10

        cls.maxDiff = 0
        cls.minDiff = cls.__scale * 100

        cls.__dfmt = "%d.%0" + str(precision) + "d" # %d.%0pd

        cls.info = "quasi-exact fixed-point decimal arithmetic (%s+%s places)" % (str(cls.precision), str(cls.guard))

    def __init__(self, arg, setval=False):
        "create a new QX object"
        if setval:
            self._value = arg                  # direct-set value
        elif isinstance(arg, (int,long)):
            self._value = arg * self.__scale  # scale incoming integers
        else:
            self._value = arg._value          # copy incoming QX
        
    #  arithmetic operations
    #
    def __add__(self, other):
        "self + other"
        v = QX(other)
        return QX(self._value + v._value, True)

    def __sub__(self, other):
        "subtract other from self"
        v = QX(other)
        return QX(self._value - v._value, True)
        
    def __neg__(self):
        "return negated self"
        return QX(-self._value, True)

    def __pos__(self):
        "return +self"
        return QX(self, True)

    def __nonzero__(self):
        "bool(self)"
        return self._value != 0

    def __abs__(self):
        "absolute value"
        return QX(abs(self._value), True)
        
    def __mul__(self, other):
        "return self * other"
        if isinstance(other, (int,long)):
            return QX(self._value * other, True)
        return QX((self._value*other._value)//self.__scale, True)
        
    def __floordiv__(self, other):
        "return self // other"
        if isinstance(other, (int,long)):
            return QX(self._value // other, True)
        return QX((self._value * self.__scale) // other._value, True)

    __div__ = __floordiv__
    __truediv__ = __floordiv__

    #  we can't have hash because a == b doesn't imply identical hashes
    def __hash__(self):
        raise NotImplementedError

    @classmethod
    def mul(cls, arg1, arg2, round=None):
        '''
        return arg1 * arg2
        round is ignored   
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        v1._value = (v1._value * v2._value) // cls.__scale
        return v1
        
    @classmethod
    def div(cls, arg1, arg2, round=None):
        '''
        return arg1 / arg2
        round is ignored
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        v1._value = (v1._value * cls.__scale) // v2._value
        return v1

    @classmethod
    def muldiv(cls, arg1, arg2, arg3, round=None):
        '''
        return (arg1*arg2)/arg3
        
        a*b/c retains the full precision of a*b.
        round is ignored
        '''
        v1 = cls(arg1)
        v2 = cls(arg2)
        v3 = cls(arg3)
        v1._value = (v1._value * v2._value) // v3._value
        return v1

    #  comparison operators
    #
    def __cmp__(self, other):
        gdiff = abs(self._value - other._value)
        if gdiff < self.__geps and gdiff > self.maxDiff:
            self.maxDiff = gdiff
        if gdiff >= self.__geps and gdiff < self.minDiff:
            self.minDiff = gdiff
        if gdiff < self.__geps:
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

    @classmethod
    def equal_within(cls, a, b, e):
        "test for equality within specified epsilon"
        return abs(a-b) < e
        
    def __str__(self):
        '''
        stringify a quasi-exact value
        print as full precision
        '''
        
        v = self._value
        gv = (v + self.__grnd) // self.__scaleg
        return QX.__dfmt % (gv // self.__scalep, gv % self.__scalep)

    @classmethod
    def report(cls):
        "Report arithmetic statistics"

        return """\
\tmaxDiff: %d  (s/b << geps)
\tgeps:    %d
\tminDiff: %d  (s/b >> geps)
\tguard:   %d
\tprec:    %d

""" % (
      cls.maxDiff,
      cls.__geps,
      cls.minDiff,
      cls.__scaleg,
      cls.__scale
      )
