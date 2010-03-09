'''
droop: profile support

copyright 2010 by Jonathan Lundell
'''

import sys

class Ballot(object):
    "one ballot"
    
    e = None

    def __init__(self, election, count=1, ranking=None):
        "create a ballot"
        self.e = election
        self.count = count            # number of ballots like this
        self.weight = self.e.V(1)     # initial weight
        self.ranks = []
        self.index = 0 # current ranking
        self.nontransferable = self.e.V(0)
        if ranking:
            for nick in ranking:
                self.addRank(nick)

    def copy(self):
        "return a copy of this ballot"
        b = Ballot(self.e, self.count, self.ranks)
        b.weight = self.weight
        b.index = self.index
        b.nontransferable = self.nontransferable
        return b

    def addRank(self, nick):
       "add a candidate to the ranking"
       assert nick not in self.ranks, 'duplicate ranking: %s' % nick
       self.ranks.append(nick)

    def advance(self, hopeful):
        "advance index to next candidate on this ballot; return True if exists"
        while self.top and self.top not in hopeful:
            self.index += 1
        return not self.exhausted

    @property
    def exhausted(self):
        "is ballot exhausted?"
        return self.index >= len(self.ranks)
    
    @property
    def top(self):
        "return top candidate, or None if exhausted"
        if self.exhausted:
            return None
        return self.e.R0.C.candidateByNick(self.ranks[self.index])
    
    @property
    def vote(self):
        "return total vote of this ballot"
        return self.weight * self.count

class Profile(object):
    "Election profile"
    
    __init = False
    
    def __init__(self, e, title, nseats=None):
        "initialize profile"
        assert not Profile.__init, 'profile already initialized'
        Profile.__init = True
        assert not nseats or nseats > 1, 'two or more seats are required'
        self.e = e
        e.profile = self
        self.title = title
        self.nseats = nseats
        self.nballots = 0
        self.ballots = []
        
    def validate(self, e):
        "check for internal consistency"
        e.R0.ballots = self.ballots
        if not self.nseats or self.nseats > e.R0.C.nHopeful:
            print 'too few candidates (%d seats; %d candidates)' % (self.nseats, e.R0.C.nHopeful)
            return False
        if self.nballots < e.R0.C.nHopeful:
            print 'too few ballots (%d ballots; %d candidates)' % (self.nballots, e.R0.C.nHopeful)
            return False
        n = 0
        for ballot in self.ballots:
            n += 1
            d = dict()
            for nick in ballot.ranks:
                if nick in d:
                    print 'candidate %s duplicated on ballot %d' % (nick, n)
                    return False
                d[nick] = nick
        return True
        
    def addBallot(self, ballot):
        "add a ballot to the list"
        self.ballots.append(ballot)
        self.nballots += ballot.count

    def bltPath(self, path):
        "process a path to a blt file"
        try:
            f = open(path, 'r')
        except IOError as emsg:
            print "droop: can't open ballot file %s (%s)" % (path, emsg)
            sys.exit(1)
        data = f.read()
        f.close()
        return self.bltData(data)
        
    def bltData(self, data):
        "process a blt blob"
        
        # see http://code.google.com/p/stv/wiki/BLTFileFormat
        # (though we don't support the OpenSTV extensions,
        # since we don't currently support any rules that need them
        #
        # we do allow /* comments */; the comment delimiters must appear
        # at the beginning and ending of their respective tokens
        #
        candidates = []
        blt = self.bltBlob(data)  # fetch a token at a time
        
        #  number of candidates
        #
        ncand = int(blt.next())

        #  number of seats
        #
        self.nseats = int(blt.next())

        #  optional: withdrawn candidates, flagged with a minus sign
        #
        withdrawn = []
        wd = int(blt.next())
        while wd < 0:
            withdrawn.append(wd)
            wd = blt.next()
        
        #  ballots
        #
        #  each ballot begins with a repetition count
        #  then a sequence of candidate numbers
        #  finally a 0 for EOL
        #
        #  a count of 0 ends the ballot list
        #
        count = wd
        while (count):
            ranking = []
            rank = int(blt.next())
            while (rank):
                ranking.append(str(rank))
                rank = int(blt.next())
            self.addBallot(Ballot(self.e, count=count, ranking=ranking))
            count = int(blt.next())
            
        #  candidates
        #
        #  a list of candidate names, quoted
        #  we know in advance how many there should be
        #
        for cand in xrange(ncand):
            candidate = blt.next()
            while not candidate.endswith('"'):
                candidate += ' ' + blt.next()
            candidates.append(candidate.strip('"'))
            
        #  election title
        #
        self.title = blt.next()
        try:
            while not self.title.endswith('"'):
                self.title += ' ' + blt.next()
        except StopIteration:
            pass
        self.title.strip('"')

        #  create the ballot objects, using candidate numbers as nicknames
        nick = 0
        for candidate in candidates:
            nick += 1
            self.e.R0.C.add(self.e, nick=str(nick), name=candidate)
        return self.validate(self.e)

    def bltBlob(self, blob):
        "parse a blt blob into tokens, skipping /* comments */"

        tokens = blob.split()
        inComment = 0
        for token in tokens:
            if token.startswith('/*'):
                inComment += 1
            if inComment:
                if token.endswith('*/'):
                    inComment -= 1
                continue
            yield token
        
