# Target Construction Playbook

The target is the expected ultimate claim cost of a policy row. The
delivered claims are valued at a fixed date, so the latest accident year is
incomplete; the methods below correct for that. They were developed in
Part 1 with four accident years. With fewer years, parts of these methods
cannot be fitted — say so, borrow explicitly, and quantify.

<!-- rule: R-0101 -->
- **Target definition.** For each policy row, `y` is the sum over linked
  claims (loss date inside the row period) of `incurred_to_date −
  recoveries`, with repudiated claims contributing zero. Open claims are
  taken at their case estimate unless R-0105 gives you a reason to adjust.
  Reconcile the sum of `y` to the cleaned claims table.

<!-- rule: R-0102 -->
- **Completion (IBNR) as an offset, from the most mature years.** Build a
  cost-weighted report-lag curve G(age) per line from the most mature
  accident years, mixing perils by their cost share and capping individual
  claims so one large loss does not shape the curve. For each row, the
  completion factor is the mean of G over the loss ages of the row's days
  at the valuation date. Use `log(exposure × completion)` as the model
  offset so that incomplete rows are weighted, not inflated. State which
  ages of the curve are observed in this market and which are assumed or
  borrowed, and the resulting completion by line for the latest year.

<!-- rule: R-0108 -->
- **Truncation-corrected lag curve as the default for short histories.**
  With fewer than three accident years, estimate the report-lag curve with a
  reverse-time product-limit estimator (each step uses only claims old
  enough to have been observed at that age), anchor it at the oldest
  well-populated age, and borrow only the share beyond the anchor from the
  reference market. Carry both the spliced curve and the no-tail variant in
  the modelling tables so the borrowed share is visible and testable.
  *(cycle 1, agent)*

<!-- rule: R-0109 -->
- **Empirical completion check from the oldest accident year.** Whenever a
  lag curve is spliced or borrowed, compare the oldest accident year's cost
  reported by twelve months with its cost reported by the valuation date
  (cost-weighted, large claims capped) against the ratio the curve implies
  for those two ages. It is the only direct test of the completion level a
  short history allows; a disagreement means the anchor or the borrowed
  share is wrong. *(cycle 2, agent)*

<!-- rule: R-0103 -->
- **Trend from mature years only.** Fit a log-linear trend of cost per
  exposure-year by line on accident years whose completion is close to
  one, and extrapolate to the prediction year. Do not fit through the
  incomplete latest year. If fewer than two mature years exist, trend
  cannot be estimated from this market: borrow a range, state it as an
  assumption, and show the sensitivity of the predicted level to it.

<!-- rule: R-0104 -->
- **Cap large losses and give the excess back as a level.** Cap row targets
  at a high quantile of positive values (Part 1 used the top 1%) and
  redistribute the capped excess as a line-level multiplier so the total
  is preserved. Models trained on capped targets are more stable; the
  multiplier restores the mean.

<!-- rule: R-0105 -->
- **Check open-claim adequacy (IBNER) but do not adopt it blind.** Compare
  average incurred of open vs closed claims by accident year and peril,
  stating first that open claims are a selected sample (large claims close
  late), and compare like with like — the older year's open claims at the
  same age, where available — before reading any implied uplift. If the
  latest year's open claims still look under-reserved relative to the
  trend of earlier years, quantify the implied uplift by line, then record
  it as an uncertainty rather than applying it, unless you have
  out-of-sample evidence. Validation years carry the same reserving bias,
  so local validation cannot confirm this adjustment. *(amended cycle 2,
  agent)*

<!-- rule: R-0106 -->
- **Late-reporting pattern of the last calendar month.** Losses in the last
  month before the valuation date are systematically under-reported. Make
  sure the completion curve, not an ad-hoc fix, carries this; mention it
  when comparing months or seasons.

<!-- rule: R-0107 -->
- **Row-level deviance decomposition.** After a first model, decompose the
  deviance into rows with zero claims, ordinary claims, and the top 1%
  largest claims. In Part 1 the zero-claim rows carried most of the score:
  frequency discrimination dominates. Use this to prioritise where to spend
  effort and to judge whether a severity refinement can matter.
