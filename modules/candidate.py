'''
Candidate and Candidates classes

Each candidate is represented by a Candidate object,
and the candidates are collected in Candidates.
'''

class Candidate(object):
    "a candidate"

    states = ['hopeful', 'elected', 'defeated', 'withdrawn']

    def __init__(self, e, name, nick=None):
        "create a candidate"
        self.e = e
        self.name = name # full name
        self.nick = nick if nick else name # nickname
        self.state = 'hopeful'
        self.vote = e.V(0)

    #  test state of this candidate
    #
    @property
    def isHopeful(self):
        "True iff hopeful candidate"
        return self.state == 'hopeful'
    @property
    def isElected(self):
        "True iff elected candidate"
        return self.state == 'elected'
    @property
    def isDefeated(self):
        "True iff defeated candidate"
        return self.state == 'defeated'
    @property
    def isWithdrawn(self):
        "True iff withdrawn candidate"
        return self.state == 'withdrawn'

    #  change state of single candidate
    #
    def elect(self, msg='Elect'):
        "elect a candidate"
        self.e.R.log("%s: %s (%s)" % (msg, self.name, self.vote))
        self.state = 'elected'
    def defeat(self, msg='Defeat'):
        "defeat a candidate"
        self.e.R.log("%s: %s (%s)" % (msg, self.name, self.vote))
        self.state = 'defeated'
    def withdraw(self, msg='Withdraw'):
        "withdraw a candidate"
        self.e.R.log("%s: %s (%s)" % (msg, self.name, self.vote))
        self.state = 'withdrawn'

    #  get/set state of this candidate
    #
    def getstate(self):
        "get state of candidate"
        return self.e.R.C._state[self.nick]
    def setstate(self, newstate):
        "set state of candidate"
        assert newstate in self.states
        self.e.R.C._state[self.nick] = newstate
    state = property(getstate, setstate)

    #  get/set vote total of this candidate
    #
    def getvote(self):
       "get current vote for candidate"
       return self.e.R.C._vote[self.nick]
    def setvote(self, newvote):
        "set vote for candidate"
        self.e.R.C._vote[self.nick] = newvote
    vote = property(getvote, setvote)

    #  get/set keep factor of this candidate
    #
    def getkf(self):
       "get current keep factor for candidate"
       return self.e.R.C._kf[self.nick]
    def setkf(self, newkf):
        "set keep factor for candidate"
        self.e.R.C._kf[self.nick] = newkf
    kf = property(getkf, setkf)

    def __str__(self):
        "stringify"
        return self.nick

    def __eq__(self, other):
        "test for equality of nickname"
        if isinstance(other, str):
            return self.nick == other
        if other is None:
            return False
        return self.nick == other.nick

class CandidateState(object):
    "candidate state for one round"

    candidates = []

    def __init__(self):
        "create candidate-state object"
        #
        #  these variables get duplicated for each round
        #
        self._vote = dict()   # votes by candidate nick
        self._state = dict()  # states by candidate nick
        self._kf = dict()     # keep factor by candidate nick

    def copy(self):
        "return a copy of ourself"
        C = CandidateState()
        C._vote = self._vote.copy()
        C._state = self._state.copy()
        C._kf = self._kf.copy()
        return C

    def add(self, e, name, nick=None):
        "add a candidate to the election"
        c = Candidate(e, name, nick)
        assert self.candidateByNick(c) is None, 'duplicate candidate'
        self.candidates.append(c)
        return c

    def candidateByNick(self, nick):
        "look up candidate by nickname"
        for c in self.candidates:
            if c.nick == nick:
                return c
        return None

    #  return list of candidates in requested state
    #
    @property
    def hopeful(self):
        "return list of hopeful candidates"
        return [c for c in self.candidates if c.isHopeful]
    @property
    def elected(self):
        "return list of elected candidates"
        return [c for c in self.candidates if c.isElected]
    @property
    def hopefulOrElected(self):
        "return list of candidates either hopeful or elected"
        return self.hopeful + self.elected
    @property
    def defeated(self):
        "return list of defeated candidates"
        return [c for c in self.candidates if c.isDefeated]
    @property
    def withdrawn(self):
        "return list of withdrawn candidates"
        return [c for c in self.candidates if c.isWithdrawn]

    #  return count of candidates in requested state
    #
    @property
    def nHopeful(self):
        "return count of hopeful candidates"
        return len(self.hopeful)
    @property
    def nElected(self):
        "return count of elected candidates"
        return len(self.elected)
    @property
    def nHopefulOrElected(self):
        "return count of hopeful+elected candidates"
        return self.nHopeful + self.nElected
    @property
    def nDefeated(self):
        "return count of defeated candidates"
        return len(self.defeated)
    @property
    def nWithdrawn(self):
        "return count of withdrawn candidates"
        return len(self.withdrawn)
