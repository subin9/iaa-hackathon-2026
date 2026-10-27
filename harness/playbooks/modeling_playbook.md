# Modelling Playbook

What the team learned about modelling this kind of synthetic insurance data
in Part 1 (four years, ≈600k training rows per line). The emerging market
has far less data, which makes the first lesson — start simple — stronger,
and the later ones (large blends, neural models) weaker. Treat every item
as a hypothesis to test under the validation playbook, not as a setting to
copy.

<!-- rule: R-0301 -->
- **Start from the simplest configuration that won.** In Part 1 the best
  tree models were extremely shallow: LightGBM Tweedie with 3 leaves,
  learning rate ≈0.02, ≈600 rounds, extra_trees on, offset
  `log(exposure × completion)`. Deeper trees learned noise; the data behave
  like a multiplicative (GLM-like) structure. Begin there and add
  complexity only when R-0202 passes.

<!-- rule: R-0312 -->
- **Re-choose capacity when volume changes by an order of magnitude — with
  an edge rule and a floor.** Pre-register a small grid of round counts
  (half, default, double) and the action when the best point sits at the
  grid edge (halve or double and re-test), so extending the grid after
  seeing a result is part of the registered procedure. Two guards: never go
  below a floor of about one hundred rounds at a learning rate of 0.02
  (fewer rounds cannot express the relativities and the gain is fold
  noise), and adopt a smaller count only if the secondary check agrees.
  Record the rule and the result even when the default wins. *(cycle 1,
  agent; amended cycle 2, agent + actuary)*

<!-- rule: R-0302 -->
- **Lean feature set.** Removing weather, sales-channel, marketing and
  calendar variables improved out-of-year performance; keeping only the
  top-K important variables made it worse. Interpretation: low-importance
  variables still carry signal, but variables whose values change by year
  do not transfer. Start lean; test re-adding groups one at a time.

<!-- rule: R-0303 -->
- **Tweedie power.** Powers 1.2–1.5 were equivalent; ≥1.7 was clearly
  worse. Do not spend time here.

<!-- rule: R-0304 -->
- **Offset-free learners.** For models without an offset hook, train on
  `y / e` with sample weight `e^(2−p)` (e = exposure × completion). This is
  exactly equivalent for Tweedie losses.

<!-- rule: R-0311 -->
- **The level check is a gate, not a report.** Put log(Σ target ÷ Σ exposure
  basis) in the init score of offset-boosted models so the trees learn
  relativities; then, after every fit, compute Σ prediction ÷ Σ target on
  the training rows. If it differs from one by more than rounding, stop:
  fix the learner (regularisation, rounds) or apply and report an explicit
  level factor — before any fold score is read. A shallow, heavily
  regularised fit on a small market can lose a double-digit share of the
  level even with a correct init score. *(cycle 1, agent; strengthened
  cycle 2, agent)*

<!-- rule: R-0305 -->
- **Blend diverse families with equal weights, seed-average each.** Part 1's
  final blend averaged shallow GBMs (Tweedie, Poisson, frequency×severity),
  a binned GLM, an additive model with few interactions, and seed-averaged
  neural tabular models. With small data, prefer fewer, more regularised
  members; each member on ≥3 seeds.

<!-- rule: R-0306 -->
- **Policy-level claim-count credibility.** Multiplying the blend by
  `(k + N) / (k + L)` — N actual prior claim count on the policy, L the
  model's expected count, k ≈ 12 — and renormalising line totals was the
  only history-based gain that held on both folds. Customer- or
  address-level pooling and amount-based versions were worse. It is
  identity for policies with no history; check how much of the test
  population that is before investing in it.

<!-- rule: R-0307 -->
- **Level matters more than shape.** The largest single gains in Part 1
  came from getting line-level (and a few segment-level) multipliers right,
  not from new models. After modelling, tabulate actual/predicted by line
  and by pre-registered segments on every fold; only segments mis-predicted
  in the same direction on all folds are candidates for a correction, and
  shrink any correction toward 1 in proportion to its noise.

<!-- rule: R-0309 -->
- **Known bias to watch.** Rows immediately after a mid-term change were
  over-predicted by 11–15% on both folds; the gain from a feature or a
  post-correction was small, but the pattern is worth checking in a new
  market.

<!-- rule: R-0310 -->
- **Compute hygiene.** Limit threads (6–8) to avoid OpenMP contention; fix
  seeds; give averaged prediction files distinct names (a seed-average
  file was once overwritten by a single-seed run); record library versions.

<!-- rule: R-0308 -->
- **Do-not-retry list (Part 1 negative results).** Each of these was tested
  properly and lost or was noise; do not repeat them unless the new market
  gives a specific reason:
  post-hoc power/isotonic recalibration (no gain; isotonic collapsed) ·
  Tweedie power ≥1.7 · adding all historical count features (worse; GBM used
  them as noise) · distillation, geometric/median blends, stacking, greedy
  (Caruana) selection (all below equal-weight mean) · double-GLM variance
  weights · separate large-loss model · Credibility Transformer (unstable) ·
  covariate-shift sample weights · seasonality / period-shape features ·
  splitting weather into address mean + yearly deviation · amount deflation
  · residual stacking across folds · top-K importance pruning · customer- or
  address-level and amount-based credibility · year-decay weights.
