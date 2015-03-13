# `Droop` Architecture #

## `Droop` design goals ##
The primary goal of `Droop` is to be able to implement STV counting rules in a native, self-contained, transparent manner.
  * A counting rule implementation is _native_ in the sense that it is implemented in its own terms, such as its legislative specification, rather than reinterpreted in the terms of the counting program.
  * While the `Droop` framework provides useful low-level tools that enable efficient and concise implementation of a counting rule, the implementation is _self-contained_, in the sense that all of its logic is contained in the particular rule implementation.
  * Once a rule implementation is complete, it should be _transparent_ in the sense that it can be seen to be correct, largely as a consequence of the above two properties.
  * A further consequence of these design goals is that rule implementations are independent. Logic changes or corrections to one rule have no impact on the other rules.
  * To verify initial and continuing correctness, the `Droop` framework includes a complete set of unit tests.

One consequence of the primary goal is that `Droop` occasionally ignores Python's DRY ("don't repeat yourself") maxim, in favor of rule self-containment.

## `Droop` framework components ##
The `Droop` framework consists of a collection of classes and functions that provide housekeeping for STV rule implementations as well as an API to external interfaces. The major components of the framework include:

  * `class ElectionProfile`: [ballot-file](BltFileFormat.md) parsing
  * `class Election`: top-level counting logic and rule support
    * `class Ballot`: internal ballot representation
  * `class Candidate`: internal candidate representation
  * `class Candidates`: the set of candidates
  * `class ElectionRecord`: maintain and report a record of an election
  * `class ElectionRule`: a specific counting rule
  * `class MethodMeek, MethodWIGM`: generic support for Meek- & WIGM-based rules
  * extensible [arithmetic](DroopArithmetic.md) support
    * `class Fixed`: fixed-point arithmetic
    * `class Guarded`: guarded-precision fixed-point arithmetic provides an efficient approximation to exact arithmetic
    * `class Rational`: exact-value arithmetic
  * uniform communication of help info from rules to UI
  * uniform communication of election parameters from UI to rules
  * unit testing
  * several built-in [rules](DroopRules.md)
  * a [command-line interface](DroopCLI.md)

Together with drop-in rule implementations, the `Droop` framework acts as an STV counting engine, with external interfaces for ballot data, election parameters and result reporting.