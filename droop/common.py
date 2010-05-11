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
import droop

droopName = 'droop'
droopVersion = '0.8'
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

def parseOptions(opts):
    "parse a list of name=value options into a dictionary"
    options = dict()
    path = None
    for opt in opts:
        optarg = opt.split('=')
        if len(optarg) == 1:
            if optarg[0] in droop.values.arithmeticNames:
                options['arithmetic'] = optarg[0]
            elif optarg[0] in droop.electionRuleNames():
                options['rule'] = optarg[0]
            elif optarg[0] == 'dump':
                options['dump'] = True
            else:
                if path:
                    raise droop.common.UsageError("multiple ballot files: %s and %s" % (path, optarg[0]))
                path = optarg[0]
                options['path'] = path
        else:
            if optarg[1].lower() in ('false', 'no'):
                options[optarg[0]] = False
            elif optarg[1].lower() in ('true' , 'yes'):
                options[optarg[0]] = True
            else:
                options[optarg[0]] = optarg[1]
    return options
