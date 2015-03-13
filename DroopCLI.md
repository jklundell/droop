# `Droop` command-line interface #
The `Droop` core logic expects its runtime options in the form of a Python dict containing a set of key="value" options. The core requires two options: "rule" and "path", specifying the counting rule and the path to the ballot file respectively.

## Droop.py ##
`Droop.py` is a general-purpose CLI for `Droop`. Command-line options are specified in the form key=value. An option with no key= specified will be recognized implicitly as rule=option or arithmetic=option if it falls into the defined set of rule or arithmetic names; otherwise it is treated as a ballot-file path (path=option).

The current `Droop.py` usage string:
```
Droop.py options ballotfile
  options:
    rule name (meek,meek-prf,mpls,qpq,scotland,warren,wigm,wigm-prf,wigm-prf-batch)
    arithmetic class name (fixed,integer,rational,guarded)
    profile=reps, to profile the count, running reps repetitions
    dump, to dump a csv of the rounds
    rule- or arithmetic-specific options:
      precision=n: decimal digits of precision (fixed, guarded)
      guard=n: guard digits (guarded; default to guard=precision)
      dp=n: display precision (rational)
      omega=n: meek iteration terminates when surplus < 1/10^omega

  help is available on the following subjects:
    arithmetic fixed guarded meek meek-prf mpls qpq rational rule scotland warren wigm wigm-prf wigm-prf-batch
```

## `mpls.py` and `scotland.py` ##
These two commands take a single argument, the path to a ballot file, and invoke the corresponding counting rule. They are examples of counting rules with no options. To run them _with_ options such as profiling or dump, use `Droop.py`.

## `oscar.py` and `irv.py` ##
These two commands are examples of informally defined rules that provide a fixed set of options to built-in generic rules.

`oscar.py` uses the WIGM counting rule and fixed arithmetic to approximate the STV rule used for counting Oscar nominations. `irv.py` uses the WIGM counting rule and integer arithmetic to count an IRV election, with a single winner and no surplus transfers.