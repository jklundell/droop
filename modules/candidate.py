'''
Candidate and CandidateState classes

Candidate holds a candidate ID and uses it to manage state in CandidateState.
CandidateState contains the per-round candidate state.
'''

class Candidate(object):
    "a candidate"

    def __init__(self, E, cid, order):
        "new candidate"
        self.E = E
        self.cid = cid     # candidate id
        self.order = order # ballot order

    #  test state of this candidate
    #
    @property
    def isHopeful(self):
        "True iff hopeful candidate"
        return self in self.E.R.C.hopeful
    @property
    def isPending(self):
        "True iff transfer-pending candidate"
        return self in self.E.R.C.pending
    @property
    def isElected(self):
        "True iff elected candidate"
        return self in self.E.R.C.elected
    @property
    def isDefeated(self):
        "True iff defeated candidate"
        return self in self.E.R.C.defeated
    @property
    def isWithdrawn(self):
        "True iff withdrawn candidate"
        return self in self.E.withdrawn
        
    @property
    def name(self):
        "candidate name"
        return self.E.cName[self.cid]

    #  get/set vote total of this candidate
    #
    def getvote(self):
       "get current vote for candidate"
       return self.E.R.C._vote[self.cid]
    def setvote(self, newvote):
        "set vote for candidate"
        self.E.R.C._vote[self.cid] = newvote
    vote = property(getvote, setvote)
    
    @property
    def surplus(self):
        "return candidate's current surplus vote"
        s = self.vote - self.E.R.quota
        return self.E.V(0) if s < self.E.V(0) else s
        
    #  get/set keep factor of this candidate
    #
    def getkf(self):
       "get current keep factor for candidate"
       if not self.E.R.C._kf: return None
       return self.E.R.C._kf[self.cid]
    def setkf(self, newkf):
        "set keep factor for candidate"
        self.E.R.C._kf[self.cid] = newkf
    kf = property(getkf, setkf)

    def __str__(self):
        "stringify"
        return self.name

    def __eq__(self, other):
        "test for equality of cid"
        if isinstance(other, str):
            return self.cid == other
        if other is None:
            return False
        return self.cid == other.cid

class CandidateState(object):
    "candidate state for one round"

    def __init__(self, E):
        "create candidate-state object"
        
        self.E = E

        self._vote = dict()   # votes by candidate cid
        self._kf = dict()     # keep factor by candidate cid
        
        self.hopeful = set()
        self.elected = set()
        self.defeated = set()

    @property
    def withdrawn(self):
        "interface to E.withdrawn for consistency"
        return self.E.withdrawn

    @property
    def pending(self):
        "set of elected candidates with transfer pending"
        _pending = set()
        for c in [b.topCand for b in self.E.R.ballots if not b.exhausted and b.topCand in self.elected]:
            _pending.add(c)
        return _pending

    def copy(self):
        "return a copy of ourself"
        C = CandidateState(self.E)
        
        C._vote = self._vote.copy()
        C._kf = self._kf.copy()
        
        C.hopeful = self.hopeful.copy()
        C.elected = self.elected.copy()
        C.defeated = self.defeated.copy()
        return C

    #  add a candidate to the election
    #
    def addCandidate(self, c, msg=None, isWithdrawn=False):
        "add a candidate"
        if isWithdrawn:
            self.E.withdrawn.add(c)
            msg = msg or 'Add withdrawn'
            self.E.R.log("%s: %s" % (msg, c.name))
        else:
            self.hopeful.add(c)
            msg = msg or 'Add hopeful'
            self.E.R.log("%s: %s" % (msg, c.name))

    def elect(self, c, msg='Elect'):
        "elect a candidate; optionally transfer-pending"
        self.hopeful.remove(c)
        self.elected.add(c)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, c.vote))
    def defeat(self, c, msg='Defeat'):
        "defeat a candidate"
        self.hopeful.remove(c)
        self.defeated.add(c)
        self.E.R.log("%s: %s (%s)" % (msg, c.name, c.vote))

    def vote(self, c, r=None):
        "return vote for candidate in round r (default=current)"
        if r is None: return self._vote[c.cid]
        return self.E.rounds[r].C._vote[c.cid]

    def isHopeful(self, c, r=None):
        "True iff candidate is hopeful in specifed round (default=current)"
        if r is None: return c in self.hopeful
        return c in self.E.rounds[r].C.hopeful

    def isPending(self, c, r=None):
        "True iff candidate is transfer-pending in specifed round (default=current)"
        if r is None: return c in self.pending
        return c in self.E.rounds[r].C.pending

    def isElected(self, c, r=None):
        "True iff candidate is elected in specifed round (default=current)"
        if r is None: return c in self.elected
        return c in self.E.rounds[r].C.elected

    def isDefeated(self, c, r=None):
        "True iff candidate is defeated in specifed round (default=current)"
        if r is None: return c in self.defeated
        return c in self.E.rounds[r].C.defeated

    def isWithdrawn(self, c):
        "True iff candidate is withdraw in specifed round (default=current)"
        return c in self.E.withdrawn

    @property
    def hopefulOrElected(self):
        "return union of hopeful and elected candidates"
        return self.hopeful.union(self.elected)

    @property
    def hopefulOrPending(self):
        "return union of hopeful and transfer-pending candidates"
        return self.hopeful.union(self.pending)

    #  return count of candidates in requested state
    #
    @property
    def nHopeful(self):
        "return count of hopeful candidates"
        return len(self.hopeful)
    @property
    def nPending(self):
        "return count of transfer-pending candidates"
        return len(self.pending)
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
        return len(self.E.withdrawn)
