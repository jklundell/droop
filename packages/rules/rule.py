'''
election rule abstract class

copyright 2010 by Jonathan Lundell
'''

class ElectionRule(object):
    '''
    abstract class for election rules
    '''
    
    @classmethod
    def help(cls, subject):
        "return help string"
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
    def reportMode(cls):
        "how should this election be reported? meek or wigm"
        return None

    @classmethod
    def count(cls, E):
        "count the election"
        pass
