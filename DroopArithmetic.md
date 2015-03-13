# `Droop` Arithmetic #

`Droop` supports fixed-point, guarded and rational arithmetic.

  * Fixed-point arithmetic is essentially integer arithmetic scaled by a specified number of decimal digits, a power of ten. Most public STV rules specify decimal-scaled fixed-point arithmetic. `Droop` allows explicit rounding, to conform to various rule specifications.

  * [Guarded arithmetic](GuardedArithmetic.md) is an extension of fixed-point arithmetic that uses additional guard digits to achieve quasi-exact calculations. That is, if sufficient precision is specified, guarded arithmetic will generate identical outcomes to exact (rational) arithmetic. Python's efficient implementation of arbitrarily large integers makes guarded arithmetic fast and practical.

  * Rational arithmetic is based on Python's `fractions.Fraction` class, and calculates all results exactly. The principle limitation of `Droop`'s rational arithmetic is that some elections will not be counted in a reasonable period of time (or memory), especially when using iterative (Meek or Warren) rules.