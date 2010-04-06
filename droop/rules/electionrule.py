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

class ElectionRule(object):
    '''
    abstract class for election rules
    '''
    
    @classmethod
    def helps(cls, helps, name):
        "add help string for rule 'name'"
        return None

    @classmethod
    def ruleNames(cls):
        "return supported rule name or names"
        return None

    @classmethod
    def options(cls, options=dict()):
        "initialize election parameters"
        return options
    
    @classmethod
    def info(cls):
        "return a brief info string for use in the election report"
        return None

    @classmethod
    def tag(cls):
        "return a string for unit tests to tag files"
        return None

    @classmethod
    def method(cls):
        "underlying method: meek or wigm"
        return None

    @classmethod
    def count(cls, E):
        "count the election"
        pass
