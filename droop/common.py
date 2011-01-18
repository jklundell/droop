# -*- coding: utf-8 -*-
'''
droop common

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

droopName = 'droop'
droopVersion = '0.11'
droopAuthor = 'Jonathan Lundell'
droopAuthorEmail = 'jlundell@prfound.org'
droopURL = 'http://prfound.org'
droopLicense = 'GNU General Public License version 3'
droopDescription = 'Counting software for STV elections',
droopLongDescription = 'Droop is a flexible counting package for STV elections.'

class UsageError(Exception):
    "command-line usage error"

class ElectionError(Exception):
    "error counting election"
