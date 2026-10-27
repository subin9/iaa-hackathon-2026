# Data Readiness Playbook

Apply these rules when profiling and cleaning the policy, customer, address,
weather and claims tables, before any target is built. They are methods the
team learned pricing the developed market (Part 1). The emerging market is
a different operational system: expect some of these checks to find
nothing and others to find things no rule anticipated. Report both.
Every treatment applied to a training table must be applied identically to
the matching test table.

## Profiling

<!-- rule: R-0001 -->
- **Recompute exposure from the period dates.** For every policy and test
  row, compute the row length in years from `period_start` and
  `period_end` and compare it with the stored `exposure`. Treat any
  disagreement beyond rounding as a finding; repair `exposure` from the
  dates. Values that look like day counts (hundreds) are the typical
  symptom. Check training and test files alike.

<!-- rule: R-0014 -->
- **Classify exposure mismatches by ratio cluster before repairing.**
  Compute stored ÷ date-derived exposure for every row and tabulate the
  ratio: clusters near 365 are day counts, near 365/360 a 360-day basis,
  near (n−1)/n an exclusive end date, near 1 rounding. Report each cluster
  as its own finding, then repair every row from the dates. A second
  convention hides behind the first when only the obvious cluster is
  checked. *(cycle 1, agent)*

<!-- rule: R-0003 -->
- **Unit-scale profiling of amount columns.** For every monetary column
  (sums insured, premiums, excesses, claim amounts), tabulate the ratio of
  each value to the column's typical level and look for mass at powers of
  ten. A cluster at ×1,000 or ×0.001 is a unit error, not an outlier: repair
  by rescaling, and record how you decided the boundary. Apply the same
  test and the same repair to the test files — a feature on the wrong
  scale in test rows corrupts those predictions directly.

<!-- rule: R-0013 -->
- **Decide unit errors per row on a proportionality ratio, not a value
  threshold.** When two amount columns should be proportional (premium and
  sum insured, paid and incurred), tabulate their ratio per row: a unit
  error in one column shows as a ratio shifted by a power of ten while the
  value alone may look merely large. The ratio rule is self-calibrating and
  applies unchanged to training, test and reference tables; a value cut-off
  is a tuned number that has to be justified. *(cycle 1, agent)*

<!-- rule: R-0002 -->
- **Content-key uniqueness of claims.** Test whether any claims repeat
  another claim exactly on (policy, peril, loss date, amounts) under a
  different `claim_id`. Deduplicate exact copies and record the count.
  If none exist, record that the check was run and found nothing — a
  negative result is part of the audit trail.

<!-- rule: R-0004 -->
- **Link claims to policy rows by loss date, then account for the rest.**
  A claim belongs to the policy row of the same `policy_id` whose period
  contains `loss_date`. Report the match rate. Investigate every unmatched
  claim before building targets: a policy that exists but has no row
  covering the loss date, or a loss date before the policy's first row,
  indicates a date or linkage defect to decide on, not a rounding issue.

<!-- rule: R-0015 -->
- **Lag-plausibility test for unlinked claims.** For claims whose loss date
  falls outside every period of their policy, compare their report lags with
  the lag distribution of the matched claims. Lags beyond the matched
  distribution's extreme quantile mark a date defect, not a late report:
  exclude those claims and raise a query rather than re-dating them, and
  state their share of incurred so the effect on levels is bounded.
  *(cycle 1, agent)*

<!-- rule: R-0007 -->
- **Valuation-date and future-information check.** Confirm the latest
  `loss_date` and `report_date` against the stated valuation date, and
  confirm that no claim falls in the test period. Note how much of the
  latest accident year's reporting is likely still outstanding (this feeds
  target construction).

<!-- rule: R-0008 -->
- **Identify dominant large losses early.** For each line and accident
  year, list claims whose net incurred exceeds a few percent of that year's
  total. One such claim can distort trend, development curves and segment
  comparisons. Do not delete them; hand them to target construction (cap
  and redistribute) and mention them wherever they affect a comparison.

## Leakage and time-identity

<!-- rule: R-0005 -->
- **Training-only tails in behavioural counts.** For every count or
  behaviour variable recorded during the policy period (service contacts,
  missed payments, mid-term events), compare its distribution in training
  rows with the test rows. A variable whose upper tail exists only in
  training, or whose value grows mechanically with the claims it is meant
  to predict, is not available at pricing time in the same form: exclude it
  from features and record why.

<!-- rule: R-0006 -->
- **Adversarial validation.** Fit a classifier to separate the latest
  training year from the test year on candidate features. Any feature that
  alone separates them almost perfectly (join year, calendar identifiers)
  is a time stamp, not a risk factor: exclude it or transform it to a
  relative quantity (tenure) that has the same meaning in both years.
  Report the residual separability after exclusions — the remaining shift
  is portfolio mix, which the shift report must explain.

<!-- rule: R-0016 -->
- **Cohort-stamp detection before multivariate adversarial validation.**
  Cross-tabulate every customer and policy attribute's value *and* its
  nullness against the join year (or first policy year). Any attribute that
  is a deterministic function of join year — including one that is null
  exactly for customers who joined before a system or campaign existed —
  is a time stamp. Confirm with a single-feature adversarial AUC, exclude
  it, and only then run the multivariate check; this orders the exclusions
  in one pass. *(cycle 1, agent)*

<!-- rule: R-0011 -->
- **Data-quality flags are not risk factors.** Columns you create to mark
  repaired or suspicious rows stay out of the feature set. Keep them in the
  modelling tables for audit, named so that they are obviously flags.

<!-- rule: R-0018 -->
- **Test whether nulls are missing at random before choosing a treatment.**
  For every column with material missingness, compare the other covariates
  of null rows with those of non-null rows (location, value, exposure
  measures). If the null group differs systematically, it carries risk
  information: keep it as its own "unknown" level rather than imputing to
  the mode, and say so. If nulls look like independent draws, no indicator
  feature is needed. *(cycle 1, actuary)*

## Final gate

<!-- rule: R-0012 -->
- **Reconcile before you move on.** Row counts of every cleaned table vs
  the as-delivered table, explained by findings; claim count and net
  incurred before vs after cleaning, explained by findings; and a one-line
  statement per table of what changed. Unexplained movement is a defect in
  the cleaning, not in the data.

<!-- rule: R-0017 -->
- **Reconciliation ladder.** Write the whole chain as one table — exposure
  (raw → cleaned), claims count and net incurred (raw → cleaned), Σ target
  (modelling tables → cleaned claims), model level (Σ prediction → Σ target
  on training rows) — and refuse to proceed while any link is open. The
  ladder is what catches a silent level drift in a model as quickly as a
  dropped row in cleaning. *(cycle 1, agent)*
