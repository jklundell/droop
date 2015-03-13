# BLT File Format #

`Droop` uses the `blt` file format, first described by Hill, Wichmann & Woodall in ["Algorithm 123 - Single Transferable Vote by Meek's method"](http://www.dia.govt.nz/diawebsite.NSF/Files/meekm/$file/meekm.pdf) (1987).

> The data file should be held on disc, or other device that allows quick `rewinding', because it has to be read many times during program execution.

> Its form should be as follows:

```
4 2
-2
3 1 3 4 0
4 1 3 2 0
2 4 1 3 0
1 2 0
2 2 4 3 1 0
1 3 4 2 0
0
"Adam"
"Basil"
"Charlotte"
"Donald"
"Title"
```

> The first line means that there are 4 candidates for 2 seats. The second line means that candidate number 2 withdrew before the count. As many candidates as necessary may be included in this line, each preceded by a minus sign. If no candidate withdrew, the line should be omitted entirely. The third line means that 3 voters put candidate 1 first, candidate 3 second, candidate 4 third, and no more. Each such list must end with a zero. The final zero ends the votes. The subsequent lines name the candidates, in the order of candidate numbers as used in the votes, and finally give a title for the election. If any of these names, or the title, is longer than 20 characters, only the first 20 will be used.

> For elections on any substantial scale, further programs are desirable to get the data into this required form. Machine-readable ballot papers would obviously be a great help if a suitable system can be devised.

## Current Extensions ##
Various implementations have added extensions to the format.

[OpenSTV](http://code.google.com/p/stv/wiki/BLTFileFormat) supports comments (# to end of line), ballot IDs, equal rankings and skipped rankings.

Wichmann's implementation adds a source and a comment field, both quoted, following the title.

Hill supports equality of preference by parenthesizing a set of rankings.

`Droop` supports the following extensions:

  1. OpenSTV-style comments (# to end of line)
  1. OpenSTV-style ballot IDs
  1. C-style comments /`*` like this `*`/, in keeping with the fact that the original format specification did not require newlines
  1. Wichmann-style source and comment fields
  1. OpenSTV-style equal rankings, in which two or more candidates can be joined with "=" instead of white space. Support for equal rankings is rule-specific.
  1. `[nick...]`: a list of candidate nicknames (initials or short names) to be used on ballot lines instead of numeric candidate indexes, the intent being to make manual ballot entry or auditing easier and less error-prone.
  1. `[tie ...]`: a list of candidate IDs or nicknames specifying a predetermined tiebreaking order
  1. `[droop ...]`: a list of `Droop`-specific options, as on the `droop` cli command line, for example `[droop rule=meek precision=8]`.

`Droop` will eventually support:

  1. a "+" modifier, similar in syntax to the existing "-" modifier for withdrawn candidates, to indicate pre-elected candidates in the context of an STV count-back for filling vacancies; alternatively the same functionality via an `[elected...]` option
  1. tolerate (ignore) OpenSTV-style skipped rankings

`Droop`'s blt parser treats newlines as ordinary whitespace, except that they're recognized as the end of an OpenSTV-style #-comment.

## Future Extensions ##
I have in mind several possible extensions to the blt format, and welcome feedback.

  1. The `[option...]` syntax (above) would be generalized to support arbitrary option extensions. The syntax would be such that, if a parser encountered an unrecognized option, it could skip it (though not necessarily with benign results). Such a format might be `[option some arbitrary text ]`, where the `]` token signals the end of the option string.
  1. `[order...]`: A list of candidate indexes or nicknames indicating the order of candidates on the original ballot paper. In this case, each ballot line is a list of the rank numbers that the voter wrote on a ballot paper, from top to bottom, using '-' to denote a skipped candidate.
  1. `[lines]`: The original blt format treats end-of-line as undifferentiated white space; this is why each ballot ends with an end-of-ballot indicator, '0'. This option would indicate a line-oriented ballot file in which the end of a ballot is implicitly the end of its line, and the terminating '0' is omitted.
  1. `[one]`: This option says that there is exactly one ballot per line, and the initial ballot-count token is omitted.
  1. `[withdrawn...]`: a list of candidate indexes or nicknames to be treated as withdrawn. Equivalent to the minus-sign syntax in the current blt format.
  1. `[elected...]`: a list of candidates to be treated as initially elected, for use in STV count-backs. Equivalent to the plus-sign convention mentioned above.
  1. `[include...]`: include an additional ballot file. This option is used when multiple ballot files are collected, for example at independent polling stations. A master file might have no ballot lines at all, but simply a list of `[include]` options, along with the candidate list, title, etc.
  1. A means of including digital signatures, and standardization of HMAC or other authentication.
  1. Provision for amending an election file in a supplementary file, keeping original authentication and signatures intact.