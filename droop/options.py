# -*- coding: utf-8 -*-
'''
droop options

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
import re
from . import electionRuleNames
from .common import UsageError
from .values import arithmeticNames

class Options(object):
    "handle election options"

    def __init__(self, options=None):
        "new Options object"
        self.cmd_options = self.normalize(options) or dict()
        self.file_options = dict()
        self.default = dict()
        self.force = dict()
        self.allowed = dict()

    @staticmethod
    def normalize(item):
        "normalize numeric options"

        # convert numeric options (precision, etc) to ints
        if isinstance(item, str):
            if re.match(r'\d+$', item):
                item = int(item)
        elif isinstance(item, dict):
            for key, value in item.iteritems():
                if isinstance(value, str) and re.match(r'\d+$', value):
                    item[key] = int(value)
        return item

    def update(self, name, value=None, file_options=False):
        "update command or file options"
        if isinstance(name, dict):
            for key, val in name.items():
                self.update(key, val, file_options)
        else:
            opts = self.file_options if file_options else self.cmd_options
            opts[name] = self.normalize(value)

    def getopt(self, optname):
        "get value of specfied option"
        optvalue = self.default.get(optname, None)          # find the default value
        optvalue = self.file_options.get(optname, optvalue) # ballot-file option overrides default
        optvalue = self.cmd_options.get(optname, optvalue)  # command option overrides ballot file
        optvalue = self.force.get(optname, optvalue)        # forced value overrides everything
        return optvalue

    def setopt(self, optname, default=None, force=False, allowed=None):
        "record default and return the value of a given option"
        self.default.setdefault(optname, self.normalize(default))
        if force:
            self.force[optname] = self.normalize(default)
        optvalue = self.getopt(optname)
        if allowed:
            self.allowed[optname] = allowed
            if optvalue not in allowed:
                raise UsageError('%s=%s; must be one of [%s]' % (optname, optvalue,
                    ",".join([str(x) for x in allowed])))
        return optvalue

    def unused(self):
        "return list of unused options"
        opts = set(self.file_options.keys()) | set(self.cmd_options.keys())
        opts -= set(('rule', 'path'))
        opts -= set(self.default.keys())
        return sorted(opts)

    def overrides(self):
        "return list of overridden options"
        overridden = list()
        opts = self.file_options.copy()
        opts.update(self.cmd_options)
        for key, val in self.force.items():
            if key in opts and opts[key] != val:
                overridden.append(key)
        return sorted(overridden)

    def record(self):
        "return a dict of all option dicts for the election record, plus a summary of effective options"
        effective = dict()
        effective.update(self.default)
        effective.update(self.file_options)
        effective.update(self.cmd_options)
        effective.update(self.force)
        return dict(cmd=self.cmd_options.copy(),
            file_options=self.file_options.copy(),
            default=self.default.copy(),
            force=self.force.copy(),
            allowed=self.allowed.copy(),
            options=effective)

    @staticmethod
    def parse(opts):
        '''
        parse a list of name=value (or bare name) options into a dictionary
        
        parse() has special knowledge of certain options that occur without a value
            (report, dump, json) are report types and the bare name implies True
            a known arithmetic name implies "arithmetic=name"
            a known rule name implies "rule=name"
            any other bare name implies "path=name"
        a value in ('false', 'no') is interpreted as False
        a value in ('true', 'yes') is interpreted as True
        '''
        options = dict()
        path = None
        for opt in opts:
            optarg = opt.split('=')
            if len(optarg) == 1:
                if optarg[0] in arithmeticNames:
                    options['arithmetic'] = optarg[0]
                elif optarg[0] in electionRuleNames():
                    options['rule'] = optarg[0]
                elif optarg[0] in ('report', 'dump', 'json'):
                    options[optarg[0]] = True
                else:
                    if path:
                        raise UsageError("multiple ballot files: %s and %s" % (path, optarg[0]))
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
