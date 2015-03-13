# Built-in rules #

`Droop` has several rule implementations, summarized below. Each rule is self-contained, in that all the "business logic" of the rule lives in the rule file itself; the `Droop` framework provides support and housekeeping. Consequently, changes to the framework do not change the logic of a rule, and a rule can be read, understood and audited as a single unit.


# Rules #

`Droop` rule implementations include generic, parameterized Meek and Weighted Inclusive Gregory Method (WIGM) rules as well as rules that conform to specific publicly defined specifications.

  * **meek-prf** is an implementation of the PR Foundation's [Reference Meek Rule](http://prfound.org/resources/reference/reference-meek-rule/).
  * **wigm-prf** is an implementation of the PR Foundation's [Reference WIGM Rule](http://prfound.org/resources/reference/reference-wigm-rule/).
  * **meek** is a generic implementation of Meek's method, with an option for the Warren variant.
  * **wigm** is a generic implementation of the Weighted Inclusive Gregory Method.
  * **mpls** is the [Minneapolis STV](http://library1.municode.com/default-test/DocView/11490/1/107/109) rule, a WIGM variant optimized for hand counting.
  * **scotland** is the [Scottish STV](http://www.opsi.gov.uk/legislation/scotland/ssi2007/pdf/ssi_20070042_en.pdf) rule, a WIGM variant.
  * **qpq** is an implementation of the [Quota Preferential by Quotient](http://www.votingmatters.org.uk/ISSUE17/I17P1.PDF) rule (not actually STV, but similar in that it uses ordinal ranking and satisfies the Droop proportionality criterion).

The generic rules can be used for ad hoc implementations (or approximations) of other rules by creating simple command-line scripts. `Droop` includes two such scripts.

  * **oscar** approximates the STV rule used for Oscar nominations
  * **irv** uses the generic WIGM rule to count single-winner (IRV/AV) elections