'''
droop: profile support

copyright 2010 by Jonathan Lundell
'''

import sys

class Ballot(object):
    "one ballot"
    
    E = None

    def __init__(self, election, count=1, ranking=None):
        "create a ballot"
        self.E = election
        self.count = count            # number of ballots like this
        self.weight = self.E.V(1)     # initial weight
        self.ranks = []
        self.index = 0 # current ranking
        self.residual = self.E.V(0)
        if ranking:
            for cid in ranking:
                self.addRank(cid)

    def copy(self):
        "return a copy of this ballot"
        b = Ballot(self.E, self.count, self.ranks)
        b.weight = self.weight
        b.index = self.index
        return b

    def addRank(self, cid):
       "add a candidate to the ranking"
       assert cid not in self.ranks, 'duplicate ranking: %s' % cid
       self.ranks.append(cid)

    def transfer(self, hopeful):
        "advance index to next candidate on this ballot; return True if exists"
        while self.topCand and self.topCand not in hopeful:
            self.index += 1
        return not self.exhausted

    @property
    def exhausted(self):
        "is ballot exhausted?"
        return self.index >= len(self.ranks)  # not meaningful for Meek
    
    @property
    def topCand(self):
        "return top candidate, or None if exhausted"
        if self.exhausted:
            return None
        return self.E.candidateByCid(self.ranks[self.index])
    
    @property
    def vote(self):
        "return total vote of this ballot"
        return self.weight * self.count

class Profile(object):
    "Election profile"
    
    __init = False
    
    def __init__(self, E, title, nseats=None):
        "initialize profile"
        assert not Profile.__init, 'profile already initialized'
        Profile.__init = True
        assert not nseats or nseats > 1, 'two or more seats are required'
        self.E = E
        E.profile = self
        self.title = title
        self.nseats = nseats
        self.nballots = 0
        self.ballots = []
        
    def validate(self, E):
        "check for internal consistency"
        E.R0.ballots = self.ballots
        if not self.nseats or self.nseats > E.R0.C.nHopeful:
            print 'too few candidates (%d seats; %d candidates)' % (self.nseats, E.R0.C.nHopeful)
            return False
        if self.nballots < E.R0.C.nHopeful:
            print 'too few ballots (%d ballots; %d candidates)' % (self.nballots, E.R0.C.nHopeful)
            return False
        n = 0
        for ballot in self.ballots:
            n += 1
            d = dict()
            for cid in ballot.ranks:
                if cid in d:
                    print 'candidate %s duplicated on ballot %d' % (cid, n)
                    return False
                d[cid] = cid
        return True
        
    def addBallot(self, ballot):
        "add a ballot to the list"
        if not ballot.exhausted:  # ignore empty ballots
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
        withdrawn = set()
        wd = int(blt.next())
        while wd < 0:
            withdrawn.add(str(-wd))
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
            self.addBallot(Ballot(self.E, count=count, ranking=ranking))
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

        #  create the ballot objects, using candidate numbers as candidate IDs (cid)
        cid = 0
        for cname in candidates:
            cid += 1
            self.E.newCandidate(cid=str(cid), cname=cname, order=cid, isWithdrawn=(cid in withdrawn))
        return self.validate(self.E)

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
        
