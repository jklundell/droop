# Guarded Arithmetic #

While `Droop` supports exact arithmethic using rationals, the computational overhead of rational arithmetic is prohibitive in many cases, leading to counts that for all practical purposes never complete. To get the considerable benefits of exact results without the overhead of rational arithmetic, `Droop` supports guarded arithmetic, a variation on fixed (scaled decimal) arithmetic. (For a discussion of the benefits accruing from the use of exact arithmetic in STV rules, see Lundell and Hill's [Notes on the Droop Quota](http://www.votingmatters.org.uk/ISSUE24/I24P2.pdf).)

Guarded values are Python long integers, scaled by a power of ten. For precision `p` and guard `g`, an integer value `v` is scaled to `v * 10**(p+g)`.  An epsilon `geps` ("guarded epsilon) is calculated as `10**g//2`. For display purposes only, values are rounded, by default, to `p` decimal places.

Results computed by guarded arithmetic are exact (identical to rational-arithmetic results) as long as two conditions are met. First, `p` must be sufficiently large that we have enough precision to distinguish between any two calculated values that are in fact different. For example, if we need to distinguish between two values that differ by 0.001, we clearly need a `p` of at least 3 or 4. Second, `g` must be sufficiently large as to "absorb" the accumulation of integer-arithmetic truncation errors.

It's not obvious a priori what the required values for `p` and `g` are, for any particular count. Fortunately, we can use rather large values by default and still perform counts in a reasonable time. The implementation of guarded arithmetic benefits greatly from Python's efficient implementation of arbitrarily large long integers; the time-cost of doubling the scale factor `p+g` is much less than a factor of 2.

Guarded arithmetic is implemented in [droop/values/guarded.py](http://code.google.com/p/droop/source/browse/droop/values/guarded.py). The most interesting piece is summarized here (the actual code has extra bells & whistles:

```
    #  comparison operators
    #
    def __cmp__(self, other):
        if abs(self._value - other._value) < Guarded.__geps:
            return 0
        if self._value > other._value:
            return 1
        return -1
```

`__cmp__` is used in turn to generate the other comparison operators.

The other interesting bits include a couple of functions that accept ints as arguments, and a handful of class methods that allow the rule to specify rounding. The latter functions are provided for compatibility with the Fixed class; Guarded does not round, instead "absorbing" its rounding errors in its guard digits.

The full implementation of `__cmp__` is:

```
    def __cmp__(self, other):
        gdiff = abs(self._value - other._value)
        if (gdiff < Guarded.__geps) and (gdiff > Guarded.maxDiff):
            Guarded.maxDiff = gdiff
        if (gdiff >= Guarded.__geps) and (gdiff < Guarded.minDiff):
            Guarded.minDiff = gdiff
        if gdiff < Guarded.__geps:
            return 0
        if self._value > other._value:
            return 1
        return -1
```

`minDiff` and `maxDiff` are included in the election report to give an indication of how close any comparison came to the dividing line between equality and inequality. Because Python's long-int arithmetic is quite efficient, it's practical to use more precision here (that is, higher values for precision and guard) than might be strictly necessary for exact results.