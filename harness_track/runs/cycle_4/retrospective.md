# Retrospective

## What went well

- Running the data-readiness playbook as a checklist found every planted-looking defect quickly and reconciled to the cent: exposure (two clusters), sums insured, pre-inception claims, cohort stamps, claims-driven service contacts, prediction-year weather. The reconciliation ladder (exposure, claims count and net incurred, Σ y) closed at every link.
- Classifying exposure mismatches by ratio cluster (R-0014) on the inclusive-day basis paid off immediately: the 360-day cluster was invisible until the day-count cluster was removed, and one short row needed a wider ratio window because 4-dp rounding blurs the ratio on tiny exposures.
- The proportionality test (R-0013) separated unit errors from large properties with an empty interval of 1.6–2.4 decades; the same rule worked unchanged on the test files and on the developed data.
- The truncation-corrected lag curve (R-0108) with the developed tail passed the only empirical test available (R-0109) within 0.3% on every line, and the no-tail column makes the borrowed share visible.
- The level gate (R-0311) caught a misbehaving learner before any score was read: the first fit lost 6–25% of level and its gain was concentrated in high-cardinality categoricals; fixing categorical handling and capacity before looking at D² avoided tuning on noise.
- Pre-registering the segment list, the optional feature groups and the rounds grid in code before running the fold (R-0207) made the single-fold evidence easier to read honestly.

## What was difficult or slow

- Windows console encoding broke every table print until stdout was forced to UTF-8; polars' aggregation name collisions and pandas 3's string dtype in LightGBM cost several reruns. Next time: set the encoding and alias every aggregate from the first script.
- Deciding whether 12% nulls were a defect or a data-capture style took the longest. The decisive checks were cheap once identified: co-missingness equal to the marginal rate, no covariate or claim-rate difference by nullness, and the within-policy null pattern (one row of a multi-row policy at the chance rate), which also revealed that most policy attributes are reconstructible from sibling rows.
- The new-business relativity swung from 1.67 to 1.28 (motor) between the two training years, and the model's value sits between them; with ~350 new-business claims a year there is no way to tell which year is representative, yet it sets 76% of the 2025 book. That question consumed more thought than any feature.
- The developed-market direction check for capacity pointed the opposite way from the emerging fold (more rounds with 20× the claims), and the rule had to be read as "direction check for method changes, not for capacity" to be useful.
- The baseline run is ~6 minutes end to end; each learner fix meant a full rerun. Caching the fold data would have saved time.

## Rules I could not apply as written

| Rule | Why it did not fit | Substitute | What was lost or left uncertain |
|---|---|---|---|
| R-0102 completion from the most mature years | no mature year: the oldest accident year is observed to 24 months only | reverse-time product-limit on 2023–24 anchored at 18 months; share beyond the anchor borrowed from developed AY 2021–22 (R-0108) | the tail (2.2% of motor cost) is assumed; the curve's shape beyond 24 months is untested here |
| R-0103 trend from mature years | one mature year; a trend needs two | developed AY 2021–23 trend, applied over 1.49 years, with a no-trend candidate | ±5%/yr on trend ⇒ ±7.5% on every line; the largest single level assumption |
| R-0105 IBNER like-for-like (older year's open claims at the same age) | a single valuation of two years has no snapshot of 2023 at 12 months | open vs closed comparison by year and peril only; nothing adopted | if 2024 case reserves are 10% light, 2024 levels are 1–3.5% light |
| R-0201 time-ordered folds (several) | two training years give one fold, and the earlier year is a survivor sample | the one fold as primary; policy-grouped split as a weaker secondary; developed fold as a direction check | no replication; the fold carries a 2023→2024 level change the model cannot know (−42% in buildings) |
| R-0202 adoption on every fold beyond the noise floor | one fold; the local noise floor is unknown | 3-seed mean, 0.001 bar, grouped check must agree in direction | "every fold" is one fold; a change that helps once has a poor replication record |
| R-0204 public-leaderboard noise | no submissions made; the agent never submits | — | nothing |
| R-0205 / R-0305 blends | one fold cannot validate blend weights or members; ~1,000 claims per home line | single seed-averaged family | blend gains of Part 1 (~0.001 D²) not realised |
| R-0306 claim-count credibility | 76% of test rows have no history; renewal rows have ≤ 2 years | dropped for the baseline | small possible gain on the 24% renewal rows |
| R-0307 segment corrections need every fold in the same direction | one fold | tabulated, none applied | the new-business over-prediction (motor A/P 0.81) is offered as candidate C instead of a correction |
| R-0311 level gate "within a few percent" | with ~1,000 claims the home-line boosters still under-shoot by 11–20% after the usual fixes | explicit level factor applied and reported | relativities come from an under-levelled fit |
| R-0312 capacity re-choice with a secondary check | the developed fold is the wrong secondary for capacity (volume differs 20×) | grouped split within the market as the secondary; developed fold reported as direction only | capacity rests on one fold plus a mixed-year check |
| R-0410 persistence of first-year policies into their second year | 2023 is a survivor extract (persistence 100% by construction) | stated as unmeasurable | the acquired book's second-year behaviour is unknown |
| R-0020 cross-tab of decision values | applied, but one value (`declined_by_insurer`) turned out to be a claim marker rather than a decision | team query | none for modelling (column not in test) |

## Judgment calls I am least sure about

1. **Excluding the 36 pre-inception claims rather than re-dating them.** Alternatives: shift loss dates forward by one year (lags become 46–200 days, plausible) or keep them as 2023 claims. Chose exclusion because every other claim's lag is consistent with its dates and re-dating invents data; 0.33% of incurred bounds the error. Settled by: the source system's audit trail for those claims.
2. **Reconstructing nulls from sibling rows, including from 2025 test rows into 2023–24 training rows.** The attribute is time-invariant in 100% of observable cases (95% for smoke alarms), so this is not target leakage, but it uses later records to fill earlier ones. Alternative: leave nulls. Settled by: the team's view on whether cleaned training tables may use later-dated records of the same policy.
3. **The anchor at 18 months and borrowing the tail.** Alternatives: anchor at 12 months (more claims, more borrowed) or 24 months (fewer claims, less borrowed). The R-0109 check cannot distinguish them beyond 24 months. Settled by: a later valuation of the same claims.
4. **Treating `new_business` / `renewal_count` as mix rather than stamps** (R-0019) and letting the model learn a new-business relativity from 876 claims that then applies to 76% of the test book. Alternative: fix the relativity at the pre-registered age-standardised value. Settled by: the broker's own loss experience for the transferred book, or the first quarters of 2025.
5. **Which candidate file is central.** A (model as fitted) was chosen as the default because it is the data; the one out-of-time fold argues for C. Settled by: the human's view of the 2023 new-business large losses.
6. **Using `written_premium` as a feature** (gain share 14–22%). It is available at pricing time and encodes the prior rating, but for the acquired book it is the broker's legacy price, whose relativities we have not seen. Settled by: comparing broker premium relativities with the model on the first 2025 claims.
7. **Not using `gender`** in the baseline although it is recorded and may carry signal. Settled by: the market's rating-factor regulation.
8. **The buildings level.** 2023 and 2024 differ by 60% because of 10 fire claims; the baseline uses the two-year average. Any value from 320 to 560 is defensible. Settled by: a cat-model or industry fire frequency for this market, or more years.

## Proposed additions to this workspace's practices

1. **Convention first, then clusters, then a wider net.** Establish the exposure convention from full-year rows, remove the dominant ratio cluster, tabulate the residual, and widen each cluster's ratio window in proportion to the rounding granularity of the stored value, because very short rows blur a fixed ratio. Applies whenever exposure is stored rounded. Prompted by a short row that fell outside the 360-day window.
2. **Sibling-stability test before imputing policy attributes.** For every nullable policy attribute, measure the share of multi-row policies carrying a single distinct value; attributes near 100% can be reconstructed from sibling rows, attributes that change yearly (per-period counts, vehicle age without a vehicle match) cannot. Record the share with the finding. Applies to any multi-year policy extract. Prompted by six reconstructible columns.
3. **Null-bin artefact check in distribution distances.** When comparing categorical distributions between groups, join on the level with nulls treated as a level, or exclude them explicitly; an outer join that drops null keys adds the null share to the distance and manufactures a "shift" in every column of a table at once. Applies to PSI and total-variation comparisons. Prompted by a spurious 0.2 distance that equalled the null rate.
4. **Capacity secondary check must come from the same volume.** When the reference market has an order of magnitude more claims, use a within-market grouped split as the secondary check for the rounds grid and keep the reference market's folds for method direction only. Applies whenever R-0312 is run in a smaller market. Prompted by the developed fold preferring double the rounds the emerging fold wanted.
5. **Year-by-year segment relativities before trusting a model's segment effect.** For every segment that dominates the prediction year (here new business), tabulate its relativity in each training year separately, capped and uncapped; if the years disagree by more than the segment's sampling error, treat the relativity as the main level hypothesis and prepare candidates across it rather than across trend. Applies to any acquired-book situation. Prompted by a 1.67 vs 1.28 swing.
6. **Level gate by line, with a learner-fix order.** Read the gate after the first fit and, if it fails, apply in order: one-vs-rest categorical splits, exclusion of categoricals whose level count exceeds a few percent of the claim count, stronger leaf regularisation, then an explicit factor; record the gate at each step. Applies to any log-link booster on a few thousand claims. Prompted by a 25% level loss driven by two categoricals.
7. **Leap-year sanity line in the profile.** State the policy-term convention (365 days) and its consequence for full-year rows in leap years before anyone filters on "ends 31 December". Applies to any date-driven exposure logic.
8. **Decision-value persistence cross-tab as a standing check** (extends R-0020): a decision value that should terminate but persists, and whose rows carry claims at 10× the base rate, is a claim marker; query it and never use it as a segment.

## Open questions and team queries

- F-06: 36 claims with loss dates before the policy's first row and 411–565-day lags — exclusion to confirm, or corrected loss dates to supply.
- F-21: meaning of `renewal_decision = declined_by_insurer` (persists; 91% carry a claim).
- F-22: `expenses.emerging` for `commission_comparison_site` is null; needed before any premium build for that channel.
- F-23: purpose of `reference_policies` (20 test rows stacked wide).
- `vehicle_age` definition: no emerging vehicle is under 3 years and the distribution is shifted +2 years against the developed market.
- `gender`: permitted as a rating factor in this market?
- Buildings level basis for 2025 (two-year average, 2024 alone, or capped with a reference fire share).
- Trend scenario (borrowed developed trend vs none) and new-business relativity (model 1.47 vs 2024-observed 1.28, motor): choose among candidates A / B / C in `outputs/baseline/`.
- Whether sibling reconstruction of nulls may use later-dated rows of the same policy.
- Whether the 2023 → 2024 fold should be restricted to policies present in both years to neutralise the survivor sample.
