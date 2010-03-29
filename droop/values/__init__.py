'''
election arithmetic values module init

copyright 2010 by Jonathan Lundell
'''

import rational, fixed, guarded

arithmeticNames = ('fixed', 'integer', 'rational', 'guarded')

class arithmeticValuesError(Exception):
    "election arithmetic value selection error"

def ArithmeticClass(options=dict()):
    "initialize a value class and return it"

    arithmetic = options.get('arithmetic', None) or 'guarded'
    if arithmetic == 'rational':
        rational.Rational.initialize(options)
        return rational.Rational
    if arithmetic in ('fixed', 'integer'):
        fixed.Fixed.initialize(options)
        return fixed.Fixed
    if arithmetic in ('guarded'):
        guarded.Guarded.initialize(options)
        return guarded.Guarded
    vals = ' '.join(arithmeticNames)
    raise arithmeticValuesError("unknown arithmetic %s\n\tuse: %s" % (arithmetic, vals))

def helps(helps):
    "build a help-string dictionary"
    helps['arithmetic'] = 'available arithmetic: %s' % ','.join(arithmeticNames)
    rational.Rational.helps(helps)
    fixed.Fixed.helps(helps)
    guarded.Guarded.helps(helps)
