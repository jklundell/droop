'''
election arithmetic values module init

Copyright 2010 by Jonathan Lundell

This file is part of Droop.

    Droop is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Droop is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Droop.  If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import absolute_import
from . import fixed, guarded, rational

arithmeticNames = ('fixed', 'integer', 'rational', 'guarded')

class ArithmeticValuesError(Exception):
    "election arithmetic value selection error"

def ArithmeticClass(options):
    "initialize a value class and return it"

    arithmetic = options.setopt('arithmetic', default='guarded')
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
    raise ArithmeticValuesError("unknown arithmetic %s\n\tuse: %s" % (arithmetic, vals))

def helps(helps):   # pylint: disable=W0621
    "build a help-string dictionary"
    helps['arithmetic'] = 'available arithmetic: %s' % ','.join(arithmeticNames)
    rational.Rational.helps(helps)
    fixed.Fixed.helps(helps)
    guarded.Guarded.helps(helps)
