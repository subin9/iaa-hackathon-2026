# Validation Playbook

These rules decide what counts as evidence. They cost the team several
false starts in Part 1 before they were written down. When a rule cannot be
applied as written in a smaller market, say so where it would have applied,
use the closest substitute, and escalate it in the retrospective.

<!-- rule: R-0201 -->
- **Time-ordered folds only.** Validate by training on years ≤ Y−1 and
  predicting year Y. Never use random K-fold across policy years: the same
  policy appears in several years and the split leaks. If only one such
  fold exists, that is the primary fold; add a policy-grouped split within
  the training years as a secondary, weaker check and label it as such.

<!-- rule: R-0202 -->
- **Adoption needs every fold in the same direction, beyond noise.** A
  change is adopted only if each available fold improves by more than the
  noise floor (Part 1: about +0.0003 in Tweedie D² per fold). Changes that
  helped on one fold almost never replicated. With a single fold, use the
  developed market's folds as a direction check for method changes, and be
  explicit that the evidence is weaker.

<!-- rule: R-0203 -->
- **Seeds before conclusions.** Single-seed noise in Part 1 was about
  ±0.001 D² — larger than most real effects. Judge any change on the mean
  of at least three seeds. A +0.0010 single-seed effect became +0.0001 on
  three seeds.

<!-- rule: R-0204 -->
- **Know the public-leaderboard noise before reading it.** Pairwise noise
  between two submissions on the Part 1 public set (33% of ≈627k rows) was
  about 0.0009. A smaller public set is noisier in proportion. Never choose
  between candidates on a public-score difference below the noise; never
  tune to the public score.

<!-- rule: R-0205 -->
- **Equal weights beat optimised weights.** Equal-weight averages of
  diverse model families were the most robust blend in Part 1; weights
  optimised on one fold were different on the next. Treat weight
  optimisation as a change that must pass R-0202.

<!-- rule: R-0207 -->
- **Fix the candidate set before you look.** When choosing segments, seeds
  or variants to examine against held-out evidence, decide the list on
  local evidence first and write it down. Choosing after seeing the
  evidence fits noise.

<!-- rule: R-0208 -->
- **Reconcile predicted level to history before any submission.** For each
  line, compare the predicted cost per exposure-year on the test rows with
  the history of the training years (raw and completion-adjusted), and
  explain the gap in one sentence per line. Levels are the largest single
  source of error in a new market.

<!-- rule: R-0206 -->
- **Say when a rule does not fit.** When a validation rule assumes
  something this market lacks (years, volume, history), record (a) the rule,
  (b) why it does not fit, (c) the substitute used, (d) what evidence is now
  weaker, in `validation.md` and in the retrospective. Silence is the
  failure mode, not the substitute.
