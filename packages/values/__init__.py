'''
election arithmetic values module init

copyright 2010 by Jonathan Lundell
'''

import rational, fixed, qx

arithmeticNames = ('fixed', 'integer', 'rational', 'qx')

class arithmeticValuesError(Exception):
    "election arithmetic value selection error"

def ArithmeticClass(options=dict()):
    "initialize a value class and return it"

    arithmetic = options.get('arithmetic', None) or 'quasi-exact'
    if arithmetic == 'rational':
        rational.Rational.initialize(options)
        return rational.Rational
    if arithmetic in ('fixed', 'integer'):
        fixed.Fixed.initialize(options)
        return fixed.Fixed
    if arithmetic in ('quasi-exact', 'qx'):
        qx.QX.initialize(options)
        return qx.QX
    vals = ' '.join(arithmeticClassNames)
    raise arithmeticValuesError("unknown arithmetic %s\n\tuse: %s" % (arithmetic, vals))

def help(subject):
    "try to find help on the requested subject"
    h = None
    if subject == 'arithmetic':
        h = 'available arithmetic: %s' % ','.join(arithmeticNames)
    h = h or rational.Rational.help(subject)
    h = h or fixed.Fixed.help(subject)
    h = h or qx.QX.help(subject)
    return h
