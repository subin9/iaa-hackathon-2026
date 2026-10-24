# Adaptation Playbook — pricing a new market with an existing approach

Written for Part 2 by the actuary. The developed-market work (Part 1) is a
source of methods and of a prior; it is not the answer. The protocol below
produces the evidence the team needs to decide, component by component,
what carries over — and to say plainly what remains uncertain.

## 1. See what changed

<!-- rule: R-0401 -->
- **Schema diff first.** Before any modelling, list for every table the
  columns only in the developed data, only in the emerging data, and those
  with the same name but a different encoding, granularity or meaning.
  Deliver a mapping table (developed value ↔ emerging value, or the common
  coarser representation). Map to the coarsest representation that both
  markets support; never invent precision the new market does not record.

<!-- rule: R-0402 -->
- **Shift report, two comparisons.** For every shared column compute a
  distribution distance (PSI or equivalent) for (a) emerging train vs
  emerging test and (b) developed vs emerging training years. Rank the
  shifts and interpret each as portfolio mix, data-definition change, or
  leakage. Mix is modelled; definition changes are mapped; leakage is
  excluded.

<!-- rule: R-0403 -->
- **Decompose into frequency, severity and peril mix.** Per line, per
  exposure-year, compare the two markets on claim frequency, average net
  incurred and the share of each peril — raw and with the valuation date
  stated. A different peril mix means different drivers matter; a different
  severity level with similar frequency points to cost or regulatory
  differences. Thin perils must be labelled thin.

<!-- rule: R-0407 -->
- **Acquired-portfolio check.** When the prediction year is dominated by a
  transferred or new-business book, compare that segment inside the
  training data (by channel, new-business flag, tenure) with the rest on
  frequency and severity, and on the distribution of declared history
  (prior claims, no-claims years). State whether the training segment is
  large enough to represent the test book and what the model will be
  extrapolating.

## 2. Decide what carries over

<!-- rule: R-0404 -->
- **One decision per component, with evidence.** Fill the adaptation
  decisions table for every component of the Part 1 approach: data-quality
  treatments, leakage exclusions, target definition, completion curve,
  trend, cap, IBNER view, feature set, schema mapping, model family and
  complexity, offset scheme, blend, credibility, line level, segment
  corrections, validation design. Each row names its evidence file and its
  remaining uncertainty. Default stance: structure and relativities
  (shape) may be borrowed from the developed market; levels (base rates,
  trend, completion of the latest year) are re-estimated from the emerging
  market, or borrowed only with a stated sensitivity.

<!-- rule: R-0405 -->
- **Borrowed assumptions are listed, not buried.** Anything taken from the
  developed market because the emerging data cannot support it (a
  development tail beyond the observed ages, a trend, a sparse peril's
  severity) goes in the "Borrowed assumptions" section with the effect on
  the predicted level by line if it is wrong by a plausible margin.

<!-- rule: R-0406 -->
- **New-business dominance changes what features mean.** When most test
  rows are new business, history-based features and policy-level
  credibility carry no information and tenure-type features take values
  the training data rarely shows. Evaluate any model specifically on the
  new-business subset of the training data and report that score next to
  the overall one.

## 3. Communicate

<!-- rule: R-0408 -->
- **Method, never answers.** When proposing a rule for the playbooks or
  writing the retrospective, describe the check and the decision
  procedure. Do not write market-specific counts, thresholds tuned to this
  data, or record identifiers into a rule.

<!-- rule: R-0409 -->
- **Uncertainty is a deliverable.** Every report ends with what remains
  uncertain, ranked by its effect on the predicted level, and what evidence
  (data, time, or a human decision) would reduce it.
