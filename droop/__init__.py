# -*- coding: utf-8 -*-
'''
election package init

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
import pkgutil
from . import rules

#  collect the names of all the rule modules in this directory
#
#  make a dict of the Rule classes by rule name

#  import everything in rules package
#
for importer, modname, ispkg in pkgutil.iter_modules(rules.__path__, rules.__name__ + '.'):
    module = __import__(modname)

#  find everything that subclasses rules._rule.ElectionRule,
#  directly or through a method class
#  __subclasses__: see Python Standard Library 5.13: Built-in Types/Special Attributes
#
ruleClasses = []
# pylint 0.22.0 doesn't know about __subclasses__  # pylint: disable=E1101
for rule in rules.electionrule.ElectionRule.__subclasses__():
    if not rule.__name__.startswith('Method'):
        ruleClasses.append(rule)
for rule in rules.electionmethods.MethodMeek.__subclasses__():
    ruleClasses.append(rule)
for rule in rules.electionmethods.MethodWIGM.__subclasses__():
    ruleClasses.append(rule)

#  ask each Rule for its names, and build a name->Rule dict
#
ruleByName = dict()
for Rule in ruleClasses:
    names = Rule.ruleNames()
    if isinstance(names, str):
        names = [names]
    for name in names:
        ruleByName[name] = Rule

def electionRuleNames():
    "return all the rule names"
    return sorted(ruleByName.keys())

def electionRule(rulename):
    "look up a Rule class by rule name"
    return ruleByName.get(rulename)
