'''
election rule abstract class

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

class ElectionRule(object):  # pragma: no cover
    '''
    ElectionRule is the parent class for all election rules,
    and defines the election-rule external API.
    
    The methods are listed in (roughly) logical calling order.
    In particular, options is called before info, tag or count.
    '''
    method = None # one of ('meek', 'wigm', 'qpq'): underlying method for report formats

    @classmethod
    def ruleNames(cls):
        '''
        Return the rule name (string) or names (list of strings).

        Multiple names are returned by rules that support rule variants
        that are distinguished by name. 
        
        For example, the generic Meek rule returns ('meek', 'warren').
        
        ruleNames is a class method, and is called before object instantiation.
        '''
        raise NotImplementedError

    @classmethod
    def helps(cls, helps, name):
        '''
        Add a help string for the named rule to the helps dict.
        
        name is one of the names returned by ruleNames().
        
        helps is a class method, and is called before object instantiation.
        '''
        raise NotImplementedError

    def __init__(self, E):
        '''
        Initialize the election-rule object.
        '''
        pass

    def options(self):
        '''
        Handle initialization of options.
        '''
        raise NotImplementedError
    
    def info(self):
        '''
        Return a brief info string (line fragment) for use 
        in droop.election.report's report heading.
        
        (Called after option)
        '''
        raise NotImplementedError

    def tag(self):
        '''
        Return a short string used by unit tests to tag file names
        to distinguish them from option-variants on the same rule.
        The tag might include the arithmetic name or precision, for
        rules that support variants thereof.
        
        (Called after option)
        '''
        raise NotImplementedError

    def count(self):
        '''
        Count the election self.E.
        
        Note that count has no return value. Results are communicated
        through the election object E, or, in the case of a terminating
        error, by raising an exception.
        
        (Called after option)
        '''
        raise NotImplementedError

    def action(self, record, action=None):
        '''
        Hook for rule-specific election action recording.
        
        See record.ElectionRecord.action() for details.
        '''
        pass

    def report(self, record, report, section, action=None):
        '''
        Hook for rule-specific election reporting.
        
        To override the default report section,
        append the section to report and return True
        
        See record.ElectionRecord.report() for details.
        '''
        pass

    def dump(self, line, action=None, cid=None, cstate=None):
        '''
        Hook for rule-specific election dumping.
        
        See record.ElectionRecord.report() for details.
        '''
        pass
