# Target construction notes — emerging market

Code: `work/p30_target.py`; numbers in `work/target_stats.json`; curves in `work/lag_curves.parquet`; tables in
`outputs/modelling_tables/{motor,buildings,contents}.parquet`. Valuation date 31 December 2024.

## 1. Target definition (R-0101)

For every policy row (train and test), `y` = Σ over claims of the row's line and `policy_id` whose `loss_date` lies
in [`period_start`, `period_end`] of (`incurred_to_date` − `recoveries`), with repudiated claims contributing 0.
Open claims enter at their case estimate (section 6 explains why no IBNER adjustment is applied). `y` is the cost
**observed at the valuation date**, not the ultimate; the ultimate is reached through the completion offset
(section 3). Test rows carry `y = null`.

Reconciliation: Σ `y` over the three modelling tables = **27,997,991.57** = net incurred of the cleaned claims table
with repudiated claims at 0 (27,997,991.57; difference 0.00). Claims linked: 9,102 non-repudiated + 120 repudiated =
9,222 = cleaned claims table. By line: motor 15,855,999 (7,048 claims), buildings 9,558,749 (1,056), contents
2,583,354 (998 non-repudiated).

Columns: `y`, `y_capped` (section 5), `y_max_claim` (largest linked claim), `n_claims`, `n_open`; `split`, `year`,
`exposure` (cleaned), `completion`, `completion_notail`, `completion_developed_curve`.

## 2. Claim–policy linkage (R-0004)

Method: join on `policy_id`, keep the row whose period contains the loss date (inclusive). 9,222 of 9,258 as-delivered
claims match exactly one row (99.6%); none matches two rows (rows of a policy never overlap). The 36 unmatched claims
all have loss dates before every period of their policy (14 to 431 days before the first row; loss years 2021–2023)
and report lags of 411–565 days against a matched p99 of 241 days; under R-0015 they are a date defect, excluded from
the cleaned claims table and raised as team query F-CLM-PREINCEPT. They total 97,099 incurred (0.33%), so no level
is affected whichever way the query is decided. Every cleaned claim links (assertion in the code).

## 3. Completion / IBNR (R-0102, R-0108)

**Why not the Part 1 method as written.** R-0102 builds the lag curve from the most mature accident years. The
emerging market has two accident years, the older of which is observed to at most 730 days and the younger to at
most 365. R-0108 (short histories) is applied instead: a reverse-time product-limit estimator (each step of the
curve uses only claims old enough to have been observed at that age), anchored at the oldest well-populated age, with
the share beyond the anchor borrowed from the developed market.

**Estimator.** For each line, claims of both accident years (non-repudiated), cost-weighted with each claim's net cost
capped at its line's 99th percentile (motor 18,774, buildings 134,945, contents 19,968) so that single large losses do
not shape the curve; weighting by cost mixes perils by their cost share automatically. Right truncation: claim *i* with
loss date *d<sub>i</sub>* is observable only if its lag ≤ *T<sub>i</sub>* = 2024-12-31 − *d<sub>i</sub>*. For ages
*t* ≤ τ, F(t)/F(τ) = Π<sub>t&lt;t<sub>j</sub>≤τ</sub> (1 − d<sub>j</sub>/R<sub>j</sub>), with
R<sub>j</sub> = Σw[lag ≤ t<sub>j</sub> ≤ T<sub>i</sub>] (Lynden-Bell / reverse Kaplan–Meier). Anchor τ = 365 days:
the risk set at 365 days still holds 3,537 / 521 / 492 claims (motor / buildings / contents), at 540 days only
1,805 / 253 / 253.

**Splice.** G(age) = F<sub>em</sub>(age | τ) × F<sub>dev</sub>(τ) for age ≤ τ, and G(age) = F<sub>dev</sub>(age)
beyond τ, where F<sub>dev</sub> is the cost-weighted (same capping rule) empirical lag distribution of developed
accident years 2021–2022 (57,311 / 13,047 / 11,649 claims, all observable to ≥ 730 days; lags above 730 days are
0.1% of developed claims and are treated as reported by 1,460 days). The no-tail variant sets F<sub>dev</sub>(τ) = 1
(nothing reported after one year). A third column uses the developed curve alone.

| Age (days) | motor: emerging cond. F(t)/F(365) | motor spliced G | motor developed F | buildings spliced G | buildings developed F | contents spliced G | contents developed F |
|---|---|---|---|---|---|---|---|
| 7 | 0.339 | 0.319 | 0.296 | 0.516 | 0.454 | 0.602 | 0.568 |
| 14 | 0.504 | 0.475 | 0.453 | 0.716 | 0.659 | 0.824 | 0.788 |
| 30 | 0.673 | 0.634 | 0.609 | 0.876 | 0.833 | 0.966 | 0.941 |
| 60 | 0.792 | 0.746 | 0.717 | 0.939 | 0.901 | 0.984 | 0.984 |
| 90 | 0.834 | 0.786 | 0.769 | 0.944 | 0.925 | 0.989 | 0.988 |
| 180 | 0.928 | 0.874 | 0.857 | 0.971 | 0.962 | 0.990 | 0.990 |
| 365 (anchor) | 1.000 | **0.942** (borrowed) | 0.942 | **0.990** | 0.990 | **0.990** | 0.990 |
| 540 | — | 0.980 (borrowed) | 0.980 | 0.998 | 0.998 | 0.999 | 0.999 |
| 730 | — | 0.995 (borrowed) | 0.995 | 1.000 | 1.000 | 1.000 | 1.000 |

Observed vs borrowed: ages 0–365 are **estimated from emerging claims** (shape) and scaled by the borrowed
F<sub>dev</sub>(365); ages beyond 365 are **entirely borrowed**. The borrowed share is large for motor (5.8% of
cost reported after one year, almost all bodily injury) and small for the property lines (1.0%). The naive emerging
empirical curve without truncation correction would say 98.7% / 99.8% / 99.6% at 365 days — it is biased upward
because long-lag claims from 2024 have not been reported yet; the reverse-time estimator removes that bias but
cannot see beyond the anchor, which is why the tail is borrowed. The count-weighted emerging curve is faster than the
cost-weighted one (motor 0.844 vs 0.673 at 30 days): large claims report later.

**Row completion.** For each row, the mean of G over the loss ages (at the valuation date) of the row's covered days;
rows after the valuation date (test) get 1.0. Exposure-weighted completion:

| Line | 2023 spliced | 2023 no-tail | 2024 spliced | 2024 no-tail | 2024 developed curve only | Lowest 2024 row (late-December inception) |
|---|---|---|---|---|---|---|
| motor | 0.976 | 1.000 | **0.827** | 0.877 | 0.813 | 0.094 |
| buildings | 0.997 | 1.000 | **0.943** | 0.953 | 0.927 | 0.157 |
| contents | 0.997 | 1.000 | **0.970** | 0.979 | 0.967 | 0.182 |

The 2023 completion is entirely the borrowed tail (all 2023 loss ages exceed 365 days). The last-month effect
(R-0106) is carried by the curve: a motor loss on 1 December 2024 is 63% reported by the valuation date, one on
24 December 32%. Modelling offset: log(exposure × completion) (R-0102), with the intercept added (R-0311).

## 4. Trend (R-0103)

Rule as written: fit a log-linear trend on accident years whose completion is close to one. Only 2023 qualifies
(completion 0.98–1.00); 2024 is 83–97% complete and the rule forbids fitting through it. **Trend cannot be
estimated from this market.** What the data show, for the record: completed burning cost 2024 / 2023 = motor 1.044,
buildings 0.631 (nine 2023 fire losses above 100k), contents 0.980 — one incomplete comparison, not a trend.

Borrowed range from the developed market (log-linear on raw burning cost 2021–2023, all ≥ 98% complete):
motor +2.1% per year, buildings +5.9%, contents +5.2%. Carried as two candidates (R-0505) rather than a point
estimate: **A — flat** (factor 1.000 to 2025) and **B — developed trend** applied for two years from the
training-years midpoint (2024.0 → 2025.5 is 1.5 years; the midpoint of the 2023 fold is 2023.5; the baseline uses two
years as the conservative bound): motor 1.043, buildings 1.126, contents 1.108. The target itself carries no trend;
the factor is applied at prediction time in the baseline so both candidates are visible.

## 5. Large losses (R-0104)

Row targets are capped at the 99th percentile of positive training `y` per line and the excess returned as a
line-level multiplier that preserves the total:

| Line | Cap (CU) | Rows capped | Σ y | Σ y_capped | Multiplier |
|---|---|---|---|---|---|
| motor | 21,148 | 61 | 15,855,999 | 14,715,370 | 1.0775 |
| buildings | 143,434 | 10 | 9,558,749 | 8,543,900 | 1.1188 |
| contents | 19,968 | 10 | 2,583,354 | 2,454,290 | 1.0526 |

Buildings gives back 12% as a level: the ten capped rows are the fire and flood losses of F-CLM-LARGE, and with 1,056
claims the cap sits on a handful of events. The multiplier is a level assumption with wide error (one more or one
fewer 300k fire moves it by ±3 points).

## 6. Open-claim adequacy / IBNER (R-0105)

Compared: average net incurred of open vs closed claims by accident year and peril, and the uplift the 2024 total
would need if every open 2024 claim settled at the 2023 closed-claim average of its peril.

| Line | Open claims 2024 | Avg open 2024 vs avg closed 2023 (main perils) | Implied uplift on 2024 net if open → closed-2023 severity |
|---|---|---|---|
| motor | 709 of 3,491 (20%) | bodily injury 11,600 vs 9,600; own damage 1,680 vs 1,085; third-party property 2,710 vs 2,420; theft 5,570 vs 3,760 | **−7.1%** |
| buildings | 136 of 537 (25%) | fire / flood open claims carry the large case estimates; subsidence 10,400 vs 17,000 | **+4.3%** |
| contents | 59 of 507 (12%) | theft 2,570 vs 2,940; flood 15,800 vs 8,470 | **−4.4%** |

Open claims already carry higher case estimates than closed claims of the same peril in motor and contents (large
claims stay open longer: a selection effect, not under-reserving), so the implied "uplift" is negative. Buildings
+4.3% rests on a dozen open fire / flood / subsidence claims. Decision: **no IBNER adjustment applied**; recorded as an
uncertainty of roughly ±5% on the 2024 level by line. Local validation cannot test it (the 2024 fold carries the same
reserving basis), which is the R-0105 reason not to adopt it blind.

## 7. Resulting target level by line and year

CU per exposure-year; "raw" = observed at valuation; "completed" = raw ÷ completion; "capped × mult" = capped
target completed and multiplied back (the quantity the baseline reproduces on training rows).

| Line | Year | Exposure | Claims | Raw burning cost | Completion | Completed (ultimate, no trend) | Completed, no-tail curve | Capped × multiplier, completed |
|---|---|---|---|---|---|---|---|---|
| motor | 2023 | 18,865 | 3,557 | 432.7 | 0.976 | 443.2 | 432.7 | 443.2 |
| motor | 2024 | 20,104 | 3,491 | 382.7 | 0.827 | 462.8 | 436.2 | 462.8 |
| buildings | 2023 | 11,373 | 519 | 514.3 | 0.997 | 515.8 | 514.3 | 515.8 |
| buildings | 2024 | 12,095 | 537 | 306.7 | 0.943 | 325.4 | 322.0 | 325.4 |
| contents | 2023 | 14,108 | 491 | 91.1 | 0.997 | 91.4 | 91.1 | 91.4 |
| contents | 2024 | 14,950 | 507 | 86.8 | 0.970 | 89.5 | 88.7 | 89.5 |

Two-year completed level (exposure-weighted): motor 453, buildings 417, contents 90. Trend candidate B would put
2025 at motor 473, buildings 470, contents 100.

## 8. Known limitations of the target

- The motor completion beyond one year (5.8% of cost) and the 2023 completion of every line are borrowed from a
  market with a different peril cost mix (bodily injury is 30% of emerging motor cost vs 38% developed): if the
  emerging tail is half the developed one, the 2024 motor ultimate falls by 3%; if double, it rises by 3%.
- 2023 is a survivor sample (F-SURVIVOR-2023): its level may understate a complete book.
- The buildings level depends on ~10 large fire / flood claims; cap multiplier and year-to-year comparison both move
  by several points with one event.
- No trend is estimable; the 2025 level carries a ±5–12% range between candidates A and B by line.
- Open-claim estimates are taken at face value (±5% by line, direction unknown).
- The 36 excluded pre-inception claims and 120 repudiated claims contribute 0; if the team re-dates the former they
  would add 0.3% to the 2023 level.
- Completion is applied per row by loss age; it does not vary by peril or segment, so rows whose peril mix differs
  from the line average (e.g. third-party-only motor cover, which has no own-damage claims) get the line curve.
- `hist_prior_claims_policy` counts only claims visible in the 2023–2024 window: it is 0 for every 2023 row and for
  every test new-business row, which conflates "no history available" with "no claims"; `hist_years_observed` says
  which it is.
