# Retrospective

## What went well

- The Part 1 data-readiness rules transferred almost one-for-one: the exposure ratio tabulation, the
  proportionality-ratio unit test, the loss-date linkage and lag-plausibility test, the persistence
  audit and the cohort-stamp cross-tab each found exactly the class of defect they were written for,
  and the negative results (duplicates, claim-amount units, test-file exposure) were cheap to record.
- Reconciliation closed at every link (row counts, claims, net incurred, Σy, model level), which
  caught one real problem early: the first baseline run lost a double-digit share of level with
  rounds, visible only because the level gate was applied before any score was read.
- The truncation-corrected lag curve agreed with the only direct empirical check available
  (cost reported by 12 months in the oldest year) within half a point on every line, so the
  completion offset rests on something testable rather than on the borrowed curve alone.
- Comparing the two markets like-for-like (fixed caps, per-peril frequency and severity) turned a
  confusing "buildings is 19% worse / motor is 26% better" into two concrete mechanisms (fire
  frequency from climate; lower compensation levels across all motor perils).

## What was difficult or slow

- The console encoding on this machine broke every script that printed a polars table until
  output was forced to UTF-8 and ASCII tables; half an hour lost. Check the first script's output
  before writing the next five.
- The developed-vs-emerging PSI was inflated by two artefacts (10% of developed motor policies have
  no customer record; emerging null rates are 12% vs 2.5%) and had to be recomputed on non-null
  values with the null rate reported separately. Next time: compute PSI on non-null values and a
  separate null-rate delta from the start.
- Deciding what the acquired book "is" took longer than any data defect: channel does not identify
  it, the only handle is new_business + a 2025 join year, and the training analogue is 15% of rows.
- The baseline needed two runs: an unguarded Tweedie booster with a 300-level categorical drifted
  off level and over-fitted with rounds on 1–7k claims. Starting with a leaf-step limit and without
  high-cardinality categoricals would have saved the first run.

## Rules I could not apply as written

| Rule | Why it did not fit | Substitute | What was lost / left uncertain |
|---|---|---|---|
| R-0102 completion from the most mature years | two accident years; the older is observed to 730 days with a thin risk set beyond 540 | R-0108 product-limit curve anchored at 540 days, tail from the developed curve; R-0109 empirical check | 2.3% of motor ultimate is borrowed; the anchor choice is a judgment (tested at 365 vs 540: completion moves < 0.01) |
| R-0103 trend from mature years | fewer than two mature years | developed 2021–23 trend as a range with sensitivity; two candidate files | ±5% (motor) to ±9% (property) on the 2025 level cannot be resolved locally |
| R-0201 time-ordered folds | only one fold exists, and its training year is a survivor sample | 2023 → 2024 as primary; policy-grouped 3-fold inside 2023–24 as a labelled weaker check | direction checks only; the fold trains on policies conditioned on renewing |
| R-0202 adoption on every fold beyond the noise floor | one fold | primary + secondary must agree in direction; otherwise keep the default | capacity for contents left at the default although the primary fold preferred fewer rounds |
| R-0204 public-leaderboard noise | no submissions made, no public set to measure | assume Part 1's 0.001 scale (same test size) | — |
| R-0105 compare the older year's open claims at the same age | one valuation snapshot, no claim history | developed market at the same valuation date | IBNER left as an uncertainty (±3.8% motor) rather than a tested adjustment |
| R-0306 claim-count credibility | 76% of test rows have no history; renewals have ≤ 2 years | dropped | nothing measurable lost now; revisit after a second renewal year |
| R-0305 / R-0205 blend of diverse families with equal weights | no fold evidence to validate members beyond noise | single family, 3 seeds | possible 0.001–0.003 D² from a blend, unverifiable here |
| R-0411 like-for-like capping | applicable as written — noted because the three caps told the same story for motor and contents but different stories for buildings (fire) | report all three caps | — |

## Judgment calls I am least sure about

1. **Excluding weather entirely** (as a 2025 calendar stamp) rather than keeping address-level
   climate. Alternatives: address means over 2023–25; raw values. Chose exclusion because every
   weather index separates 2024 from 2025 alone and Part 1 found weather hurt out-of-year; the climate
   signal that matters (hail, fire, frost) is partly carried by region. Settled by a group re-add test
   on the fold and, properly, by a second out-of-time year.
2. **Treating the 36 unlinked claims as date defects** rather than genuine late reports. Chose
   exclusion because their lags are beyond the 99th percentile for perils with 20–90-day tails and
   their loss dates precede any policy row; effect 0.33% of cost. Settled by the source system.
3. **Not applying a new-business relativity to contents** although the data shows 1.2–1.3× and the
   model prices ≈1.0×. Chose not to on one fold (R-0202); the alternative raises the contents test
   level ≈17%. Settled by a human decision or the 2025 experience.
4. **The anchor at 540 days and the 50k cap in the lag curve.** Measured: the anchor (365 / 540 /
   730 days) moves 2024 motor completion by less than 0.01 (0.809 / 0.804 / 0.813), but the cap
   matters more — 25k gives 0.823 and 100k 0.789, i.e. ±2.5% on the 2024 motor ultimate level,
   because the cap decides how much weight the late-reported bodily-injury claims carry. Buildings
   moves by at most 0.011 and contents by 0.002 across the same grid. A cap tied to the line's own
   large-loss cap (21k motor) would push completion up and the ultimate down; 50k was kept as the
   mid-point and the range is stated in target_notes.md.
5. **Borrowing the developed trend at full weight in the primary file.** The alternative (no trend)
   is the second file; an actuary might prefer half weight. Settled only by 2025 claims.
6. **Normalising occupation by stripping the uniform "Self-employed" prefix.** The uniform rate
   across bases (including "retired", "student", "unemployed") is strong evidence of corruption, but a
   genuine self-employment flag with a random-looking distribution would be lost; kept as a dq flag so
   it can be restored.
7. **Keeping `gender` as a feature.** It ranks in the top six by gain in motor; whether it may be used
   for pricing is a regulatory question outside the data.

## Proposed additions to this workspace's practices

- **Print the exposure-ratio tabulation on an inclusive-day basis first.** When the stored
  convention is (end − start + 1)/365, a ratio computed on the exclusive basis spreads short rows
  across 1.00–2.00 and hides the 360-day spike. Rule: determine the dominant convention from
  full-year rows, then tabulate the ratio on that basis before classifying clusters. Prompted by the
  first exposure pass, which showed a smear instead of two spikes.
- **PSI on non-null values plus a separate null-rate delta.** A distribution distance that puts
  nulls in a bin reports a data-capture difference (different null rates) as a shift in every column
  of a table at once; a reference table with unmatched join keys does the same. Rule: when several
  unrelated columns show the same PSI, suspect the null bin or a join, not the data. Prompted by the
  ≈0.16 and ≈0.70 plateaus in the developed-vs-emerging comparison.
- **Level gate before capacity choice, with a leaf-step limit for Tweedie boosters on small data.**
  On a few thousand claims an unguarded log-link booster can lose a double-digit share of level and
  D² can fall with rounds; re-choose capacity only after the learner holds its level within a few
  percent, and exclude categoricals whose level count is comparable to the claim count. Prompted by
  the first baseline run.
- **Identify the acquired book explicitly before modelling.** Check whether channel, a join-year or
  a new-business flag singles out the transferred portfolio; if none does, state which training
  segment is the analogue, its size in claims, and its age-standardised relativity, and compare the
  model's relativity to it after fitting (R-0410 applied as a pre-registered table, not a footnote).
- **Treat 2025 (prediction-year) weather as a calendar stamp by default.** Test each weather index
  alone against the train/test label; when the prediction year's values differ for every address,
  the index is a year effect for the model and should be excluded or replaced by an address-level
  climate summary.
- **Record the "label-does-not-terminate" check in the persistence audit.** Cross-tabulate each
  end-of-period decision value with presence in the following year; a value that should end a
  policy but shows near-complete persistence is a semantic defect to query, not a risk segment.
- **Carry two completion variants in the modelling tables (spliced and no-tail)** so the borrowed
  share is visible and the sensitivity can be re-run without rebuilding the curve.
- **Reconciliation ladder as a script output, not prose.** Having every link (exposure, claims,
  net incurred, Σy, model level, holdout level) printed by the pipeline made the final check a
  read-through instead of a recomputation.

## Open questions and team queries

Flagged `team_query` in findings.json:
- F-08: 36 claims with loss dates before the policy's first row and 411–565-day lags — date defects
  or genuine late reports? (0.33% of cost.)
- F-17: `commission_comparison_site` is null in the expense table while 5% of policies use that
  channel — missing loading or mislabelled channel?
- F-18: `declined_by_insurer` policies persist into the next year (167 of 181 in 2024) — what does
  the label mean in this system?
- F-24: `vehicle_age` has a floor of 3 — a definition difference or a market with no new vehicles?

Other open questions:
- Does the transferred broker book behave like our new business (motor ×1.48, contents ×1.2–1.3) or
  like our renewal book? This is the largest level question for 2025 (±21% motor).
- Should 2023's buildings fire experience (49 claims, 55% of the year's cost) be treated as a
  cat-like event and loaded through the 12% cat-reinsurance line rather than averaged into the
  base rate?
- Which trend candidate to select (submission.csv vs submission_no_trend.csv), and whether half
  weight on the developed trend is preferred.
- Is `gender` an admissible rating factor in this market?
- Is 2025 weather to be used at all (it is known at pricing time but shifts every address)?
- The 2024 open bodily-injury reserves (38% of motor 2024 cost): any claims-department view on
  adequacy would replace the ±3.8% uncertainty.
- Should the developed data be used as additional training rows (with the mapped schema) for the
  property lines where emerging claims are thin? Not done in the baseline; the shift report shows
  shape similarity but level differences that would need an explicit market offset.
