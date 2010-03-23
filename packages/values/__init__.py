'''
election arithmetic values module init

copyright 2010 by Jonathan Lundell
'''

def ArithmeticClass(options=dict()):
    "initialize a value class and return it"

    arithmetic = options.get('arithmetic', None) or 'quasi-exact'
    if arithmetic == 'rational':
        from rational import Rational
        Rational.initialize(options)
        return Rational
    if arithmetic in ('fixed', 'integer'):
        from fixed import Fixed
        Fixed.initialize(options)
        return Fixed
    if arithmetic in ('quasi-exact', 'qx'):
        from qx import QX
        QX.initialize(options)
        return QX
    return None
