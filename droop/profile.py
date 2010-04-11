'''
droop: election profile support

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

import array
import re

class ElectionProfileError(Exception):
    "error processing election profile"


class ElectionProfile(object):
    '''
    Election profile
    
    Given a path to a blt-format ballot file, or such a file's contents,
    create and return an election profile instance.
    
    The resulting election profile is passed to Election for counting.
    
    The public interface of ElectionProfile:
    
    title: the title of the election from the ballot file
    nSeats: the number of seats to be filled
    nBallots: the number of ballots (possibly greater than len(rankings) because of 
              ballot multipliers)
    eligible: the set of non-withdrawn candidate IDs 
    withdrawn: the set of withdrawn candidate IDs
    candidateName(cid): maps candidate ID to candidate name
    candidateOrder(cid): maps candidate ID to ballot order
    ballotLines: a tuple of BallotLine objects, each with a:
       multiplier: a repetition count >=1
       ranking: a tuple of candidate IDs
    
    candidates and withdrawn should be treated as frozenset; that is, unordered and immutable,
       though they may be implemented as any iterable.
       
    All attributes should be treated as immutable.
    '''
    
    def __init__(self, path=None, data=None):
        "initialize profile"
        self.title = None
        self.source = None
        self.comment = None
        self.nSeats = None
        self.nBallots = 0
        self.eligible = set()
        self.withdrawn = set()
        self._candidateName = dict()  # cid => candidate name
        self._candidateOrder = dict() # cid -> ballot order
        self.ballotLines = tuple()
        self.tieOrder = None          # tiebreaking cid sequence

        if path:
            data = self.__bltPath(path)
        if not data:
            raise ElectionProfileError('no profile data')
        self.__bltData(data)
        self.__validate()

    class BallotLine(object):
        "one ballot line"
        
        __slots__ = ('multiplier', 'ranking')
        
        def __init__(self, multiplier, ranking, nCand):
            "create a ballot-line object"
            self.multiplier = multiplier
            self.ranking = array.array('B' if nCand<=256 else 'H', ranking)
            
    def __validate(self):
        "check for internal consistency"
        if not self.nSeats or self.nSeats > len(self.eligible):
            raise ElectionProfileError('too few candidates (%d seats; %d candidates)' % (self.nSeats, len(self.eligible)))
        if self.nBallots < len(self.eligible):
            raise ElectionProfileError('too few ballots (%d ballots; %d candidates)' % (self.nBallots, len(self.eligible)))
        n = 0
        for ranking in (bl.ranking for bl in self.ballotLines):
            n += 1
            d = dict()
            for cid in ranking:
                if cid in d:
                    raise ElectionProfileError('candidate ID %s duplicated on ballot line %d' % (cid, n))
                d[cid] = cid
    
    def compare(self, other):
        "compare this profile (self) to other (unittest support)"
        if self.title != other.title: return 'title mismatch'
        if self.nSeats != other.nSeats: return 'nSeats mismatch'
        if self.nBallots != other.nBallots: return 'nBallots mismatch'
        if self.eligible != other.eligible: return 'eligible mismatch'
        if self.withdrawn != other.withdrawn: return 'withdrawn mismatch'
        for cid in self._candidateName:
            if self._candidateName[cid] != other._candidateName[cid]: return 'candidate name mismatch'
        for cid in self._candidateOrder:
            if self._candidateOrder[cid] != other._candidateOrder[cid]: return 'candidate order mismatch'
        if len(self.ballotLines) != len(other.ballotLines): return 'ballot-line count mismatch'
        for b, bo in zip(self.ballotLines, other.ballotLines):
            if b.multiplier != bo.multiplier: return 'ballot-line multiplier mismatch'
            if b.ranking != bo.ranking: return 'ballot-line ranking mismatch'
        return False

    def candidateName(self, cid):
        "get name of candidate"
        return self._candidateName[cid]
        
    def candidateOrder(self, cid):
        "get ballot order of candidate"
        return self._candidateOrder[cid]
    
    def __bltPath(self, path):
        "open a path to a blt file"
        try:
            f = open(path, 'r')
            data = f.read()
        except Exception as emsg:
            raise ElectionProfileError("can't open ballot file %s (%s)" % (path, emsg))
        f.close()
        return data
        
    def __bltData(self, data):
        "process a blt file"
        
        # see http://code.google.com/p/stv/wiki/BLTFileFormat
        # (though we don't support the OpenSTV extensions,
        # since we don't currently support any rules that need them
        #
        # we do allow /* comments */; the comment delimiters must appear
        # at the beginning and ending of their respective tokens
        #
        digits = re.compile(r'\d+')
        sdigits = re.compile(r'-?\d+')

        blt = self.__bltBlob(data)  # fetch a token at a time
        
        #  number of candidates, eligible or withdrawn
        #
        tok = blt.next()
        if not digits.match(tok):
            raise ElectionProfileError('bad first blt item "%s"; expected number of candidates' % tok)
        ncand = int(tok)

        #  number of seats
        #
        tok = blt.next()
        if not digits.match(tok):
            raise ElectionProfileError('bad second blt item "%s"; expected number of seats' % tok)
        self.nSeats = int(tok)

        #  optional: withdrawn candidates, flagged with a minus sign
        #
        self.withdrawn = set()
        tok = blt.next()
        while True:
            if not sdigits.match(tok):
                raise ElectionProfileError('bad blt item "%s" near first ballot line; expected decimal number' % tok)
            wd = int(tok)
            if wd >= 0:
                break
            self.withdrawn.add(-wd)
            tok = blt.next()
        
        #  ballots
        #
        #  each ballot begins with a multiplier
        #  then a sequence of candidate IDs 1..n
        #  finally a 0 for EOL
        #
        #  a multiplier of 0 ends the ballot list
        #
        self.ballotLines = list()
        
        while True:
            if not digits.match(tok):
                raise ElectionProfileError('bad blt item "%s" near ballot line %d; expected decimal number' % (tok, len(self.ballotLines)+1))
            multiplier = int(tok)
            if not multiplier:  # test end of ballot lines
                break
            ranking = list()
            while True:
                tok = blt.next()  # next ranked candidate or 0
                if not digits.match(tok):
                    raise ElectionProfileError('bad blt item "%s" near ballot line %d; expected decimal number' % (tok, len(self.ballotLines)+1))
                cid = int(tok)
                if not cid:  # test end of ballot
                    break;
                if cid > ncand:
                    raise ElectionProfileError('bad blt item "%s" near ballot line %d is not a valid candidate ID' % (tok, len(self.ballotLines)+1))
                ranking.append(cid)
            if ranking:                         # ignore empty ballots
                self.ballotLines.append(self.BallotLine(multiplier, ranking, ncand))
                self.nBallots += multiplier
            tok = blt.next()  # next multiplier or 0
            
        #  candidate names
        #
        #  a list of candidate names, quoted
        #  we know in advance how many there should be
        #
        for cid in xrange(1, ncand+1):
            name = blt.next()
            if not name.startswith('"'):
                raise ElectionProfileError('bad blt item "%s" near candidate name #%d; expected quoted string' % (name, cid))
            while not name.endswith('"'):
                name += ' ' + blt.next()
            if cid not in self.withdrawn:
                self.eligible.add(cid)
            self._candidateName[cid] = name.strip('"')
            self._candidateOrder[cid] = cid
            
        #  election title or options
        #  election title
        #
        tok = blt.next()
        while tok.startswith('='):
            if tok == '=tie':
                tieOrder = dict()
                o = 0
                while True:
                    o += 1
                    tok = blt.next()
                    if not digits.match(tok):
                        raise ElectionProfileError('bad blt item "%s" reading =tie option; expected decimal number' % (tok, len(self.ballotLines)+1))
                    cid = int(tok)
                    if not cid:
                        break
                    if cid > ncand:
                        raise ElectionProfileError('bad blt: =tie item "%d" is not a valid candidate ID' % cid)
                    tieOrder[cid] = o
                if len(tieOrder) != ncand:
                    raise ElectionProfileError('bad blt: =tie tiebreak sequence must list each candidate ID exactly once')
                self.tieOrder = tieOrder
            else:
                raise ElectionProfileError('bad blt item "%s": unknown option' % tok)
            tok = blt.next()

        #  election title
        #
        if not tok.startswith('"'):
            raise ElectionProfileError('bad blt item "%s" near election title; expected quoted string' % tok)
        try:
            s = tok
            while not s.endswith('"'):
                s += ' ' + blt.next()
        except StopIteration:
            raise ElectionProfileError('bad blt item "%s" near election title; expected quoted string' % s)
        self.title = s.strip('"')
        
        #  optional election-source string
        #
        try:
            tok = blt.next()
        except StopIteration:
            return
        if not tok.startswith('"'):  # ignore unquoted material at end of file
            return
        try:
            s = tok
            while not s.endswith('"'):
                s += ' ' + blt.next()
        except StopIteration:
            raise ElectionProfileError('bad blt item "%s" near election source; expected quoted string' % s)
        self.source = s.strip('"')

        #  optional comment string
        #
        try:
            tok = blt.next()
        except StopIteration:
            return
        if not tok.startswith('"'):  # ignore unquoted material at end of file
            return
        try:
            s = tok
            while not s.endswith('"'):
                s += ' ' + blt.next()
        except StopIteration:
            raise ElectionProfileError('bad blt item "%s" near election comment; expected quoted string' % s)
        self.comment = s.strip('"')

    def __bltBlob(self, blob):
        '''
        parse a blt blob into tokens
        
        skip /* comments */ and # comments (if not in quoted strings)
        '''
        lines = blob.splitlines()
        inComment = 0
        inQuote = False
        for line in lines:
            tokens = line.split()
            for token in tokens:
                if not inComment and token.startswith('"'):
                    inQuote = True
                if inQuote and token.endswith('"'):
                    inQuote = False
                if not inQuote and token.startswith('/*'):
                    inComment += 1
                if inComment:
                    if token.endswith('*/'):
                        inComment -= 1
                    continue
                # if not in quote or comment, # means comment to end-of-line
                if token.startswith('#'):
                    break
                yield token
