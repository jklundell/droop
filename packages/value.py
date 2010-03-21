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
            from values.rational import Rational
            Rational.initialize(options)
            return Rational
        if arithmetic in ('fixed', 'integer'):
            from values.fixed import Fixed
            Fixed.initialize(options)
            return Fixed
        if arithmetic in ('quasi-exact', 'qx'):
            from values.qx import QX
            QX.initialize(options)
            return QX
