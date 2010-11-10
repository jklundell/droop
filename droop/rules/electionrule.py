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
    ElectionRule is the parent class for all election rules.
    It serves as an API container; there is no ElectionRule object.
    
    The methods are listed in (roughly) logical calling order.
    In particular, options is called before info, tag or count.
    '''
    
    @classmethod
    def ruleNames(cls):
        '''
        Return the rule name (string) or names (list of strings).

        Multiple names are returned by rules that support rule variants
        that are distinguished by name. 
        
        For example, the generic Meek rule returns ('meek', 'warren').
        '''
        return None

    @classmethod
    def method(cls):
        '''
        Return a string from ('meek', 'wigm', 'qpq')
        that indicates the rule's underlying method;
        used for determining certain report formats
        '''
        return None

    @classmethod
    def helps(cls, helps, name):
        '''
        Add a help string for the named rule to the helps dict.
        
        name is one of the names returned by ruleNames().
        '''
        return None

    @classmethod
    def options(cls, options=dict(), used=set(), ignored=set()):
        '''
        Handle initialization of options.
        
        options: dict of options from command line, blt file, etc
        used: rules add the keys of options that they pay attention to
        ignored: rules add the keys of options that they explicitly ignore
        
        After options have been processed by the active rule and 
        arithmetic class, options, used & ignored are employed to
        report specified but unused or ignored (overridden) options.
        
        'ignored' is generally used for options such as precision
        that are specified by the rule itself, such as arithmetic
        and precision in the Minneapolis STV rule.
        
        options will include at least one member: rule=name.
        
        An option is reported if it is specified and either not used
        or ignored. See droop.election.report.
        '''
        return options
    
    @classmethod
    def info(cls):
        '''
        Return a brief info string (line fragment) for use 
        in droop.election.report's report heading.
        
        (Called after option)
        '''
        return None

    @classmethod
    def tag(cls):
        '''
        Return a short string used by unit tests to tag file names
        to distinguish them from option-variants on the same rule.
        The tag might include the arithmetic name or precision, for
        rules that support variants thereof.
        
        (Called after option)
        '''
        return None

    @classmethod
    def count(cls, E):
        '''
        Count the election E.
        
        Note that count has no return value. Results are communicated
        through the election object E, or, in the case of a terminal
        error, by raising an exception.
        
        (Called after option)
        '''
        pass
