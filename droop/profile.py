# -*- coding: utf-8 -*-
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
import codecs

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
    ballotLines: a list of BallotLine objects, each with a:
       multiplier: a repetition count >=1
       ranking: an array of candidate IDs
    ballotLinesequal: a list of BallotLine objects, each with a:
       multiplier: a repetition count >=1
       ranking: tuple of tuples of candidate IDs
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
        self.nCand = None
        self.nBallots = 0
        self.eligible = set()
        self.withdrawn = set()
        self._candidateName = dict()  # cid => candidate name
        self._candidateOrder = dict() # cid -> ballot order
        #
        #  ballotLines is a list of BallotLine objects for ballots with no equal rankings
        #    ranking is an array of cids
        #  ballotLinesEqual is a list of BallotLine objects with at least one equal ranking
        #    ranking is a tuple of tuples of cids
        #
        self.ballotLines = list()
        self.ballotLinesEqual = list()
        self.lineNumber = 0           # line number during parsing
        self.tieOrder = dict()        # tiebreaking cid sequence: cid->order
        self.nickCid = dict()         # nick to cid
        self.nickName = dict()        # cid to nick
        self.options = list()         # list of options for main counter

        if path:
            data = self._bltPath(path)
        if not data:
            raise ElectionProfileError('no profile data')
        self._bltData(data)
        self.__validate()
        if not self.nickCid:          # create default nicknames: str(cid)
            for cid in xrange(1, self.nCand+1):
                self.nickCid[str(cid)] = cid
                self.nickName[cid] = str(cid)
        if not self.tieOrder:         # create default tie-break order: cid
            for cid in xrange(1, self.nCand+1):
                self.tieOrder[cid] = cid

    class BallotLine(object):
        "one ballot line"
        
        __slots__ = ('multiplier', 'ranking', 'line')
        
        def __init__(self, profile, multiplier, ranking):
            '''
            create a ballot-line object
            
            ranking is a list of lists of cids
            remove any withdrawn candidates
            if all the cid-lists are singletons, store an array
            else store the list (as a tuple)
            '''
            self.multiplier = multiplier
            self.line = profile.lineNumber
            equal_rank = False
            for rank in ranking:
                for cid in set(rank):
                    if cid in profile.withdrawn:
                        rank.remove(cid)
                if len(rank) > 1:
                    equal_rank = True
            ranking = [rank for rank in ranking if len(rank)]   # strip empty ranks
            if len(ranking) == 0:
                self.ranking = None     # empty ballot line
            elif equal_rank:
                profile.nBallots += multiplier
                self.ranking = tuple(ranking)
            else:
                profile.nBallots += multiplier
                ranking = [rank[0] for rank in ranking] # possibly empty
                self.ranking = array.array('B' if profile.nCand<=256 else 'H', ranking)
            
    def __validate(self):
        "check profile for internal consistency"
        if not self.nSeats or self.nSeats > len(self.eligible):
            raise ElectionProfileError('too few candidates (%d seats; %d candidates)' % (self.nSeats, len(self.eligible)))
        if self.nBallots < len(self.eligible):
            raise ElectionProfileError('too few ballots (%d ballots; %d candidates)' % (self.nBallots, len(self.eligible)))
        for bl in self.ballotLines:
            d = dict()
            for cid in bl.ranking:
                if cid in d:
                    raise ElectionProfileError('candidate ID %s duplicated on line %d' % (cid, bl.line))
                d[cid] = cid
        for bl in self.ballotLinesEqual:
            d = dict()
            for rank in bl.ranking:
                for cid in rank:
                    if cid in d:
                        raise ElectionProfileError('candidate ID %s duplicated on line %d' % (cid, bl.line))
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
        if len(self.ballotLinesEqual) != len(other.ballotLinesEqual): return 'ballot-line (equal) count mismatch'
        for b, bo in zip(self.ballotLines, other.ballotLines):
            if b.multiplier != bo.multiplier: return 'ballot-line multiplier mismatch'
            if b.ranking != bo.ranking: return 'ballot-line ranking mismatch'
        for b, bo in zip(self.ballotLinesEqual, other.ballotLinesEqual):
            if b.multiplier != bo.multiplier: return 'ballot-line (equal) multiplier mismatch'
            if b.ranking != bo.ranking: return 'ballot-line (equal) ranking mismatch'
        return False

    def candidateName(self, cid):
        "get name of candidate"
        return self._candidateName[cid]
        
    def candidateOrder(self, cid):
        "get ballot order of candidate"
        return self._candidateOrder[cid]
    
    def _bltPath(self, path):
        "open a path to a blt file"
        try:
            f = open(path, 'r')
            data = f.read()
        except Exception as emsg:
            raise ElectionProfileError("can't open ballot file %s (%s)" % (path, emsg))
        f.close()
        return data

    def getCid(self, nick, loc):
        '''
        convert a nick (or cid) to a cid, and validate the cid
        
        If nick is an int (or a decimal string), validate and return it.
        Otherwise, it's a nickname; look it up and return the cid.
        
        loc is used for error messages if the nickname is unknown 
        or theresulting cid is out of range
        '''
        if isinstance(nick, str) and re.match(r'\d+$', nick):
            nick = int(nick)
        if isinstance(nick, int):
            if nick > 0 and nick <= self.nCand:
                return nick
        elif self.nickCid and nick in self.nickCid:
            return self.nickCid[nick]
        if isinstance(loc, int):
            raise ElectionProfileError('bad blt: bad candidate ID %s near ballot %d' % (nick, loc))
        raise ElectionProfileError('bad blt: bad candidate ID %s in %s' % (nick, loc))

    def __bltOptionNick(self, option_name, option_list):
        '''
        process a blt [nick option line
        
        we require a list of exactly nCand unique nicknames
        '''
        if len(option_list) != self.nCand:
            raise ElectionProfileError('bad blt: [nick] nickname list must list each candidate exactly once')
        self.nickCid = dict()
        self.nickName = dict()
        cid = 0
        for nick in option_list:
            cid += 1
            if nick in self.nickCid:
                raise ElectionProfileError('bad blt: duplicate nickname: %s' % nick)
            self.nickCid[nick] = cid
            self.nickName[cid] = nick
        
    def __bltOptionTie(self, option_name, option_list):
        "process a blt [tie option line"
        self.tieOrder = dict()
        o = 0
        for tok in option_list:
            o += 1
            cid = self.getCid(tok, '[tie] option')
            self.tieOrder[cid] = o
        if len(self.tieOrder) != self.nCand:
            raise ElectionProfileError('bad blt: [tie] tiebreak sequence must list each candidate exactly once')

    def __bltOption(self, option, blt):
        "process a blt option line"
        option_name = option.lstrip('[')
        option_list = list()
        if option_name.endswith(']'):
            option_name = option_name.rstrip(']')
        else:
            while True:
                tok = blt.next()
                if tok != ']':
                    option_list.append(tok.rstrip(']'))
                if tok.endswith(']'):
                    break
        if option_name == 'tie':
            self.__bltOptionTie(option_name, option_list)
        elif option_name == 'nick':
            self.__bltOptionNick(option_name, option_list)
        elif option_name == 'droop':
            self.options.extend(option_list)
        else:
            raise ElectionProfileError('bad blt item "%s": unknown option' % option)

    def _bltData(self, data):
        "process a blt data blob, catching iteration exceptions"
        try:
            self.__bltData(data)
        except StopIteration:
            raise ElectionProfileError('bad blt file: unexpected end-of-file')

    def __bltData(self, data):
        "process a blt blob"

        digits = re.compile(r'\d+$')
        sdigits = re.compile(r'-?\d+$')

        blt = self.__bltBlob(data)  # fetch a token at a time
        
        #  number of candidates, eligible or withdrawn
        #
        tok = blt.next().lstrip(codecs.BOM_UTF8) # strip utf-8 BOM from first token
        if not digits.match(tok):
            raise ElectionProfileError('bad first blt item "%s"; expected number of candidates' % tok)
        self.nCand = int(tok)

        #  number of seats
        #
        tok = blt.next()
        if not digits.match(tok):
            raise ElectionProfileError('bad second blt item "%s"; expected number of seats' % tok)
        self.nSeats = int(tok)

        #  optional:
        #    withdrawn candidates, flagged with a minus sign
        #    general options, flagged with an equal sign
        #
        self.withdrawn = set()
        tok = blt.next()
        while True:
            if tok.startswith('['):     # look for an option
                self.__bltOption(tok, blt)
            elif tok.startswith('('):   # look for a ballot ID
                break
            elif sdigits.match(tok):    # look for a withdrawn candidate or multiplier
                wd = int(tok)
                if wd >= 0:
                    break
                self.withdrawn.add(-wd)
            else:
                raise ElectionProfileError('bad blt item "%s" near first ballot line; expected decimal number' % tok)
            tok = blt.next()

        #  ballots
        #
        #  each ballot begins with a multiplier or ballot ID,
        #  then a sequence of candidate IDs 1..n
        #  finally a 0 for EOL
        #
        #  a multiplier of 0 ends the ballot list
        #
        self.ballotLines = list()
        ballotIDs = set()
        
        while True:
            if tok.startswith('('):
                bid = tok
                while not bid.endswith(')'):
                    bid += ' ' + blt.next()
                bid = bid.lstrip('(').rstrip(')').strip(' ')
                if bid in ballotIDs:
                    raise ElectionProfileError('duplicate ballot ID %s' % bid)
                ballotIDs.add(bid)
                multiplier = 1
            elif digits.match(tok):
                multiplier = int(tok)
            else:
                raise ElectionProfileError('bad blt item "%s" near line %d; expected decimal number' % (tok, self.lineNumber))
            if not multiplier:  # test end of ballot lines
                break

            ranking = list()
            while True:
                tok = blt.next()  # next ranked candidate or 0
                if tok == '0':
                    break   # end of ballot
                toks = tok.split('=')
                ranking.append([self.getCid(c, len(self.ballotLines)+1) for c in toks])

            if ranking:                         # ignore empty ballots
                ballot = self.BallotLine(self, multiplier, ranking)
                if isinstance(ballot.ranking, tuple):
                    self.ballotLinesEqual.append(ballot)
                elif ballot.ranking is not None:
                    self.ballotLines.append(ballot)

            tok = blt.next()  # next multiplier or 0
            
        if len(ballotIDs) and len(ballotIDs) != len(self.ballotLines):
            raise ElectionProfileError('number of ballot IDs (%d) does not match number of ballots (%d)' % (len(ballotIDs), len(self.ballotLines)))

        #  candidate names
        #
        #  a list of candidate names, quoted
        #  we know in advance how many there should be
        #
        for cid in xrange(1, self.nCand+1):
            try:
                name = blt.next()
            except StopIteration:
                raise ElectionProfileError('bad blt item "%s" near candidate name #%d; expected quoted string' % (name, cid))
            if not name.startswith('"'):
                raise ElectionProfileError('bad blt item "%s" near candidate name #%d; expected quoted string' % (name, cid))
            while not name.endswith('"'):
                name += ' ' + blt.next()
            if cid not in self.withdrawn:
                self.eligible.add(cid)
            self._candidateName[cid] = name.strip('"')
            self._candidateOrder[cid] = cid
            
        #  election title
        #
        tok = blt.next()
        if not tok.startswith('"'):
            raise ElectionProfileError('bad blt item "%s" near election title; expected quoted string' % tok)
        try:
            s = tok
            while not s.endswith('"'):
                s += ' ' + blt.next()
        except StopIteration:
            raise ElectionProfileError('bad blt item "%s" near election title; expected quoted string' % s)
        self.title = s.strip('"').strip(' ')
        
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
        self.source = s.strip('"').strip(' ')

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
        self.comment = s.strip('"').strip(' ')

    def __bltBlob(self, blob):
        '''
        parse a blt blob into tokens
        
        skip /* comments */ and # comments (if not in quoted strings)
        '''
        lines = blob.splitlines()
        inComment = 0
        inQuote = False
        lineNumber = 0
        for line in lines:
            lineNumber += 1
            tokens = line.split()
            for token in tokens:
                if not inComment and token.startswith('"'):
                    inQuote = True
                if inQuote and token.endswith('"'):
                    inQuote = False
                    yield token
                    continue
                if not inQuote and token.startswith('/*'):
                    inComment += 1
                if inComment:
                    if token.endswith('*/'):
                        inComment -= 1
                    continue
                # if not in quote or comment, # means comment to end-of-line
                if not inQuote and token.startswith('#'):
                    break
                yield token
