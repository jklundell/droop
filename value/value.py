'''
Abstract base for other Value classes

'''

class Value(object):
    "a Value class that implements rationals"

    exact = None

    @staticmethod
    def ArithmeticClass(arithmetic, precision, guard):
        "initialize a value class and return it"
        if arithmetic == 'rational':
            import rational
            V = rational.Value
        elif arithmetic == 'qx':
            import qx
            V = qx.Value
            V.init(precision, guard)  # set precision & guard in decimal digits
        elif arithmetic == 'fixed':
            import fixed
            V = fixed.Value
            V.init(precision)  # set precision in decimal digits
        elif arithmetic == 'integer':
            import integer
            V = integer.Value
            V.init()
        else:
            raise ValueError('unknown arithmetic %s' % arithmetic)
        return V

    @classmethod
    def info(cls):
        "return description of arithmetic method"
        return "value.Value must be subclassed"
        
    def __init__(self, arg):
        "create a new Value object"
        self._value = None

    #  Value.init(precision) must be called before using the class
    #
    @classmethod
    def init(cls):
        "initialize class variables"
        pass

    #  arithmetic operations
    #
    #  Note that these ops do not alter self,
    #  but rather return the result with no side effect.
    #
    def __add__(self, other):
        "self + other"
        v = self.__class__(other)
        v._value += self._value
        return v

    def __sub__(self, other):
        "subtract other from self"
        v = self.__class__(other)
        v._value = self._value - v._value
        return v
        
    def __neg__(self):
        "return negated self"
        v = self.__class__(self)
        v._value = -v._value
        return v

    def __pos__(self):
        "return +self"
        return self.__class__(self)

    def __nonzero__(self):
        "bool(self)"
        return self._value != 0

    def __mul__(self, other):
        "return self * other"
        raise TypeError('value.Value must be subclassed')
        
    def __floordiv__(self, other):
        "return self / other"
        raise TypeError('value.Value must be subclassed')

    __div__ = __floordiv__
    __truediv__ = __floordiv__
    
#     def _plus_(self, other):
#         "return self + other"
#         v = self.__class__(other)
#         v._value += self._value
#         return v
#         
#     def _minus_(self, other):
#         "subtract other from self"
#         v = self.__class__(other)
#         v._value = self._value - v._value
#         return v
#         
#     def _negate_(self):
#         "return negated self"
#         v = self.__class__(self)
#         v._value = -v._value
#         return v

    #  multiplication & division with rounding
    #
    def _times_(self, other, round=None):
        "return self * other"
        raise TypeError('value.Value must be subclassed')
        
    def _over_(self, other, round=None):
        "return self / other"
        raise TypeError('value.Value must be subclassed')

    def _times_over_(self, mul, div, round=None):
        "return (self*mul)/div"
        raise TypeError('value.Value must be subclassed')


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
