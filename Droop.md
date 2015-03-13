# Introduction to `Droop` #

`Droop` is a Python-based package for counting STV elections.

The primary motivation for `Droop` is to provide a framework for implementing STV counters in a manner that facilitates verification and certification. Rule implementations are self-contained and independent of other rules. Rules can, in general, be expressed in terms of their statutory language. Extensive and extensible unit tests provide additional validation support.

`Droop`'s features include:

  * STV rule implementations are self-contained, for clarity and straightforward validation
  * `Droop`'s framework provides housekeeping support tailored for STV implementation, keeping the rule implementations uncluttered.
  * The framework includes interchangeable [arithmetic](DroopArithmetic.md) support for integer, decimal fixed-point, [guarded](GuardedArithmetic.md) decimal fixed-point (quasi-exact) and rational (exact) arithmetic.
  * `Droop` includes implementations of several STV rules, including reference rules from the [Proportional Representation Foundation](http://prfound.org) and an example implementation of Minneapolis MN's STV rule; more are planned.
  * Parametric implementations of Meek, Warren and Weighted Inclusive Gregory (WIGM) methods are available, so that ad hoc rules can be easily assembled and compared from the user interface.
  * New rule implementations can be "dropped in" without any changes to the framework.
  * The framework, rule implementations and user interface are decoupled; not only are new rule implementations easy to add, but so are new user interfaces. The current implementation includes a general-purpose [CLI](DroopCLI.md) as well as examples of specialized CLI interfaces for specific rules. A web-based UI is planned but not yet implemented.
  * The framework and rule implementations are readily embedded as an STV counting engine in third-party software.
  * All IO treated as UTF-8.

See DroopArchitecture for an overview of `Droop`'s structure.

Currently (v0.11), the unit tests run correctly on OS X 10.6.6 (with Python 2.6.1 and 2.7.1) and RHEL5 (Python 2.6.5).