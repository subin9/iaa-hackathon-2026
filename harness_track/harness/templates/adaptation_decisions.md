# Adaptation decisions — what carries over from Part 1

One row per component. "Carry over" is one of: AS-IS (used unchanged),
ADAPTED (method kept, parameters or inputs changed), RE-ESTIMATED (method
kept, values re-fitted on emerging data), BORROWED (taken from the
developed market because emerging data cannot support it), DROPPED.
Evidence names the file or table that supports the decision. Remaining
uncertainty says what could still be wrong and, where you can, how much
the predicted level moves if it is (sensitivity).

| Component | Part 1 choice | Carry over | Evidence | Remaining uncertainty / sensitivity |
|---|---|---|---|---|
| Data-quality treatments (exposure, unit scale, duplicates, linkage) | | | | |
| Leakage exclusions (in-period behaviour counts, join-year identifiers) | | | | |
| Target definition (net incurred, repudiated = 0) | | | | |
| Completion / IBNR curve (source years, tail) | | | | |
| Trend (fit years, extrapolation to 2025) | | | | |
| Large-loss cap and redistribution | | | | |
| IBNER view on open claims | | | | |
| Feature set (lean vs full; new/missing columns) | | | | |
| Schema mapping (age bands, construction codes, free text) | | | | |
| Model family and complexity (tree depth, regularisation) | | | | |
| Offset / weighting scheme | | | | |
| Blend composition and weights | | | | |
| Policy-level claim-count credibility | | | | |
| Line-level level (base rate) | | | | |
| Segment-level corrections | | | | |
| Validation design (folds, noise floor, seeds) | | | | |

## What changed in this market (summary)
(Three to six sentences: customers, climate, regulation/cost signals you
can see in the data, portfolio mix of the test year.)

## Borrowed assumptions — list and sensitivity
(Each item taken from the developed market: what, why, and the effect on
predicted level by line if it is wrong by a plausible margin.)

## Open decisions for the team
