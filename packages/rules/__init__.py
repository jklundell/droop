'''
election rules module init

copyright 2010 by Jonathan Lundell
'''

import os

#  collect the names of all the rule modules in this directory:
#    name.py where name does not have a leading underscore
#
#  make a dict of the Rule classes by module name
#  make a dict of the Rule classes by rule name
#
mydir = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
modules = [os.path.splitext(name)[0] for name in os.listdir(mydir) if name.endswith('.py') and not name.startswith('_')]

RuleByModule = dict()
RuleByName = dict()
for module in modules:
    Rule = __import__(module, globals()).Rule
    RuleByModule[module] = Rule
    names = RuleByModule[module].ruleNames()
    if isinstance(names, str):
        names = [names]
    for name in names:
        RuleByName[name] = Rule

def electionRuleNames():
    "return all the rule names"
    return sorted(RuleByName.keys())

def electionRule(name):
    "look up a Rule class by rule name"
    return RuleByName[name]
    
def helps(helps):
    "add election rules to the help-string dictionary"
    helps['rule'] =  'available rules: %s' % ','.join(electionRuleNames())
    for name in electionRuleNames():
        RuleByName[name].helps(helps, name)
