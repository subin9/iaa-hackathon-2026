# Target construction notes — emerging market

Script: `work/c02_targets.py` (curves in `work/lib_curve.py`; statistics in `work/target_stats.json`, curves in `work/curves.json`). Tables: `outputs/modelling_tables/{motor,buildings,contents}.parquet`.

## 1. Target definition and reconciliation (R-0101)

For each training row, `y` = Σ over claims linked to the row of (`incurred_to_date` − `recoveries`), with `status = repudiated` contributing 0 (their amounts are already 0). Open claims at case estimate (§6). Amounts as valued at 31 December 2024; `y` is the **reported** amount, and `completion` carries the IBNR correction as an offset, so `y` is not grossed up. Test rows have `y` null and `completion` 1.0 (expected-ultimate basis).

Reconciliation: Σ y = 15,855,887.96 (motor) + 9,558,749.31 (buildings) + 2,583,354.30 (contents) = **27,997,991.57 = net incurred of the cleaned claims table** (exact, repudiated = 0). Raw claims net incurred was 28,090,258.83; the 92,267.26 difference is the 36 unlinked claims excluded in cleaning (F-06).

Also in the tables: `y_cap` (capped target, §5), `n_claims`, `n_claims_nonrep`, `n_open`, `max_claim`, `completion_notail` (§3), data-quality flags `dq_*` (not features), excluded columns renamed `x_*` (not features), optional weather means `wx_*_mean2324` (optional feature group, off in the lean baseline).

## 2. Claim–policy linkage (R-0004)

A claim belongs to the row of the same `policy_id` whose [period_start, period_end] contains `loss_date`. 9,222 of 9,258 claims (99.6%) link to exactly one row; none to two. The 36 unlinked claims all have loss dates before their policy's first row and report lags of 411–565 days (matched p99.5 = 334 d): a date defect, excluded, 0.33% of incurred, team query (R-0015).

## 3. Completion / IBNR (R-0102, R-0108, R-0109)

**Method.** Cost-weighted report-lag curve G(age) per line (perils mixed by their cost share), each claim weighted by its net incurred capped at the line's 99th percentile (motor 18,774, buildings 134,945, contents 19,968 CU) so one large loss does not shape the curve. With only two accident years the lag data are right-truncated, so the curve is the **reverse-time product-limit estimator** (each step uses only claims old enough to have been observable at that age), anchored at **540 days (18 months)**, the oldest well-populated age: the risk set there still holds 1,805 motor, 253 buildings and 253 contents claims (25–29% of each line's cost). The share reported beyond the anchor is **borrowed** from the developed market's own product-limit curve on accident years 2021–2022 (36–48 months observable): G_dev(540) = 0.9778 motor, 0.9984 buildings, 0.9995 contents. Beyond 540 days the spliced curve follows the developed curve's shape.

Row completion = mean of G over the loss ages (valuation date − day) of the row's days; days after the valuation date count 1.0. `completion` uses the spliced curve, `completion_notail` the emerging-only curve with G(540) = 1, so the borrowed share is visible and the sensitivity can be re-run without rebuilding (R-0108).

**Observed vs borrowed.**

| Line | G at 30 / 90 / 180 / 365 d (spliced) | Observed in this market | Borrowed from developed | 2024 mean completion (spliced / no-tail) | 2023 mean completion |
|---|---|---|---|---|---|
| motor | 0.636 / 0.788 / 0.877 / 0.945 | ages 0–540 d (shape) | 2.2% of cost beyond 540 d, and the shape 540–1,365 d | **0.829** / 0.848 | 0.974 |
| buildings | 0.880 / 0.949 / 0.976 / 0.995 | ages 0–540 d | 0.16% beyond 540 d | **0.948** / 0.949 | 0.998 |
| contents | 0.967 / 0.990 / 0.991 / 0.991 | ages 0–540 d | 0.05% beyond 540 d | **0.970** / 0.971 | 0.998 |

The naive (truncation-biased) emerging ECDF would give G(365) = 0.987 for motor against 0.945 corrected — the uncorrected curve would overstate 2024 motor completion by about 4 points. The developed market's own curve gives G(365) = 0.939 for motor, 0.989 buildings, 0.992 contents: the emerging shapes are slightly faster (more short-lag glass/hail, fewer bodily-injury claims).

**Empirical check (R-0109).** For accident year 2023, cost reported within 12 months of loss ÷ cost reported by the valuation date (capped): motor **0.974 observed vs 0.971 implied** by the spliced curve (0.975 no-tail); buildings 0.997 vs 0.997; contents 0.993 vs 0.993. The anchor and the borrowed share are consistent with the only direct test the data allow; the test cannot see beyond 24 months.

**Effect on 2024 level.** Motor 2024 burning cost 382.7 raw → 461.5 per exposure-year after completion (451.2 with the no-tail curve: the borrowed tail is worth 2.3% of the motor level). Buildings 306.7 → 323.6; contents 86.8 → 89.5.

## 4. Trend (R-0103)

Only one emerging accident year (2023) is near-complete; 2024 is at 83–97%. With fewer than two mature years, trend **cannot be estimated from this market** (R-0103 as written does not apply). The local two-point check, completion-adjusted: motor 2024/2023 = 461.5 / 444.3 = +3.9%, buildings 323.6 / 515.2 = −37% (fire-driven, meaningless as a trend), contents 89.5 / 91.3 = −2%.

**Borrowed** from the developed market: log-linear fit of completion-adjusted, capped (99th percentile) cost per exposure-year on accident years 2021–2023 (2024 excluded as incomplete): motor **×0.995 / yr** (frequency ×0.981, severity rising), buildings **×1.065 / yr** (frequency ×1.016), contents **×1.049 / yr** (frequency ×1.018). Extrapolation from the exposure-weighted mid-point of the training rows to that of the test rows: 1.49 years (computed from the row dates; test business incepts through 2025) → motor ×0.992, buildings ×1.099, contents ×1.074.

These are assumptions, not estimates; the baseline applies them as a central scenario and reports the no-trend scenario as the alternative candidate (R-0505). Sensitivity: ±5%/yr on the trend moves the 2025 level by ±7.5% per line.

## 5. Large losses (R-0104)

Row targets capped at the 99th percentile of positive training-row targets per line; the excess is returned as a line multiplier so the total is preserved.

| Line | Cap (CU) | Rows capped | Excess (CU) | Redistribution multiplier |
|---|---:|---:|---:|---:|
| motor | 21,148 | 61 | 1,139,900 | 1.0775 |
| buildings | 143,434 | 10 | 1,015,049 | 1.1188 |
| contents | 19,968 | 10 | 129,154 | 1.0526 |

Buildings: 10 rows (all fire or flood) hold 11% of the line's cost; the multiplier is the line's large-loss load and is itself uncertain (10 events). Dominant claims identified in F-10 were not deleted.

## 6. Open-claim adequacy — IBNER (R-0105)

Open claims are a selected sample: 2024 motor open claims average 4,088 CU against 1,724 closed (2023: 11,164 vs 1,958); buildings 2024 open 9,463 vs closed 6,043; open bodily-injury claims average 11,539, open fire 33,666, open flood (buildings) 33,508. Paid ÷ incurred on open claims is 0.18–0.34, i.e. 65–80% of open incurred is case reserve. The like-for-like comparison the rule asks for — the older year's open claims at the same age — is not observable in a two-year extract valued once (2023's open claims are now at 12–24 months; we have no snapshot of them at 0–12 months). 2023's remaining open claims (130 motor, 21 buildings, 0 contents) show no sign of under-reserving relative to the closed population of the same perils, but that is the survivors' view. **No IBNER uplift applied**; recorded as an uncertainty. If 2024 case reserves are 10% light, the 2024 motor level is 2% light (open share of 2024 incurred 20%) and buildings 3.5%.

## 7. Resulting target level by line and year (per exposure-year; cleaned exposure)

| Line | Year | Exposure | Claims | Frequency | Raw burning cost (y / exposure) | ÷ completion (spliced) | ÷ completion (no tail) | Capped y / exposure | Mean completion |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| motor | 2023 | 18,864.5 | 3,557 | 0.1886 | 432.7 | 444.3 | 436.4 | 400.1 | 0.974 |
| motor | 2024 | 20,104.0 | 3,491 | 0.1736 | 382.7 | 461.5 | 451.2 | 356.6 | 0.829 |
| buildings | 2023 | 11,372.6 | 519 | 0.0456 | 514.3 | 515.2 | 514.6 | 446.3 | 0.998 |
| buildings | 2024 | 12,095.4 | 537 | 0.0444 | 306.7 | 323.6 | 323.1 | 286.7 | 0.948 |
| contents | 2023 | 14,107.7 | 491 | 0.0348 | 91.1 | 91.3 | 91.3 | 87.6 | 0.998 |
| contents | 2024 | 14,950.3 | 507 | 0.0339 | 86.8 | 89.5 | 89.4 | 81.5 | 0.970 |

For comparison the raw burning cost on the **as-delivered** exposure (what `check_sub.py` prints without `--cleaned`) is 307.7 / 275.8 motor, 312.0 / 246.7 buildings, 70.0 / 63.2 contents by year (2023 / 2024) — 20–40% below the cleaned history because of the day-count exposures (R-0507).

Expected 2025 level before any model, central scenario (two-year completed average × trend to 2025.5): motor ≈ 453 × 0.992 ≈ **450**; buildings ≈ 417 × 1.099 ≈ **458** (range 320–560 depending on which year's fire experience one believes); contents ≈ 90 × 1.074 ≈ **97**. These exclude the new-business relativity (1.17–1.33 on frequency/cost for 76% of the test book), which the model must supply.

## 8. Known limitations of the target

- Reported-basis target with an offset: the model learns relativities from incomplete 2024 rows weighted down by completion; if the completion shape differs by segment (e.g. young drivers with more bodily injury) the row-level offset is slightly mis-specified. Perils are mixed by cost share at line level only.
- The tail beyond 18 months (2.2% of motor cost) and the trend are borrowed; trend is the larger uncertainty (±7.5% per ±5%/yr).
- Buildings: 1,056 claims, 70 fires carrying 45% of cost. The level is not credible to better than ±25%; the cap multiplier (1.12) rests on 10 rows.
- IBNER not applied; 2024 case reserves are 65–80% of open incurred.
- 2023 is a survivor sample: its frequency is that of policies that renewed into 2024.
- The 36 excluded pre-inception claims (0.33%) could in principle belong to rows the extract does not contain; if they were genuine 2023 claims with mis-keyed years the 2023 level is 0.6% light.
- No claims after 29 Dec 2024 and none in 2025: the target contains no information about the test period itself; everything about 2025 is extrapolation.
