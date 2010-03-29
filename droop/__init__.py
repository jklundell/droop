'''
election package init

copyright 2010 by Jonathan Lundell
'''

import pkgutil
import rules

#  collect the names of all the rule modules in this directory
#
#  make a dict of the Rule classes by rule name

#  import everything in rules package
#
for importer, modname, ispkg in pkgutil.iter_modules(rules.__path__, rules.__name__ + '.'):
    module = __import__(modname)

#  find everything that subclasses rules._rule.ElectionRule
#
ruleClasses = []
for rule in rules.electionrule.ElectionRule.__subclasses__():
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

def electionRule(name):
    "look up a Rule class by rule name"
    return ruleByName.get(name, None)
