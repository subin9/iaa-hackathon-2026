# Target construction notes — emerging market

Code: `work/p30_target.py` (inputs `./outputs/cleaned/`, outputs `./outputs/modelling_tables/{motor,buildings,contents}.parquet`, statistics `work/target_stats.json`, curves `work/curves.json`). Valuation date 31 December 2024. Column dictionary for the modelling tables: `outputs/modelling_tables/README.md`.

## 1. Target definition and reconciliation

`y` for a policy row = Σ over claims of that policy with loss_date inside [period_start, period_end] of (incurred_to_date − recoveries), all perils, open claims at their case estimate, repudiated claims contributing zero (they carry zero incurred in this market, F-08). `y` is the cost reported by the valuation date, i.e. ultimate × completion; it is not grossed up. Test rows have `y` null.

| line | train rows | rows with y > 0 | linked claims | Σ y (modelling table) | net incurred of cleaned claims, excl. repudiated | difference |
|---|---|---|---|---|---|---|
| motor | 47,283 | 6,091 | 7,048 | 15,855,887.96 | 15,855,887.96 | 0 |
| buildings | 27,447 | 1,011 | 1,056 | 9,558,749.31 | 9,558,749.31 | 0 |
| contents | 34,566 | 969 | 998 | 2,583,354.30 | 2,583,354.30 | 0 |
| total | 109,296 | 8,071 | 9,102 | 27,997,991.57 | 27,997,991.57 | 0 |

The total equals the cleaned claims table's net incurred excluding repudiated claims (27,997,991.57, profile.md §7); the as-delivered total was 28,090,258.83, the gap being the 36 excluded pre-inception claims (F-07). 120 repudiated claims carry zero and are linked but add nothing.

## 2. Claim-policy linkage

A claim belongs to the row of the same policy_id whose period contains the loss_date (R-0004). On the cleaned tables 9,222 of 9,222 claims (100%) link to exactly one row; none link to two rows (rows of a policy never overlap) and the claim's line always equals the row's line. As delivered the match rate was 9,222 of 9,258 (99.6%); the 36 unmatched claims all had loss dates 14-431 days before the policy's first row with report lags of 411-565 days (99.5th percentile of matched lags is 73-344 days by line) and were excluded rather than re-dated (F-07, team query). Net incurred excluded 92,267 (0.33%); had they belonged to the first row of their policy, the 2023 level would rise by about 0.6% in motor and 0.3% in property.

## 3. Completion (IBNR)

Method (R-0102, adapted for two years). For each line a cost-weighted report-lag distribution G(a) = share of ultimate cost reported within a days of the loss was estimated from the 2023-2024 claims of that line, each claim weighted by its net incurred capped at the line's 99th percentile (18,625 / 138,765 / 20,065) so no single loss shapes the curve; perils are mixed by their cost share automatically. Because lags are right-truncated at the valuation date (a December 2024 loss can only show lags ≤ 30 days), the curve is estimated by the reverse-time product-limit method: the step P(lag ≤ d | lag ≤ d+1) uses only claims old enough to observe lags up to d+1, and the steps are chained downward from an anchor age. The anchor is 540 days: the emerging data determine the shape of the curve up to 540 days (1,810 motor, 253 buildings and 253 contents claims are at least 540 days old), and the share of ultimate cost reported after 540 days is borrowed from the developed market, estimated with the same method on its four accident years and assumed complete at 1,440 days.

| line | G(30d) | G(90d) | G(180d) | G(365d) | G(540d) = developed share by 540 d (borrowed) | G(730d) borrowed | observed part | borrowed part |
|---|---|---|---|---|---|---|---|---|
| motor | 0.637 | 0.790 | 0.878 | 0.947 | 0.979 | 0.993 | shape 0-540 d from 7,048 claims | 2.1% of ultimate cost beyond 540 d (bodily injury) |
| buildings | 0.881 | 0.950 | 0.976 | 0.995 | 0.998 | 1.000 | shape 0-540 d from 1,056 claims | 0.2% beyond 540 d |
| contents | 0.967 | 0.990 | 0.991 | 0.991 | 0.9997 | 1.000 | shape 0-540 d from 998 claims | 0.03% beyond 540 d |

Emerging reporting is faster than developed at every age (motor within 365 days: 96.7% of the within-540 cost vs 94.6% developed), so borrowing the developed tail is conservative (it adds IBNR). Row completion = mean of G over the ages (valuation date minus each day of the row); rows starting after the valuation date (all test rows) have completion 1. The offset for training is log(exposure × completion / trend_factor) (§4), so incomplete rows are down-weighted, never inflated.

Resulting completion by line and year (exposure-weighted): motor 2023 0.975, 2024 0.831; buildings 0.998 / 0.948; contents 0.9985 / 0.970. Alternative with no borrowed tail (curve assumed complete at 540 days, column `completion_alt`): motor 0.992 / 0.848, buildings 0.999 / 0.950, contents 0.999 / 0.971. The tail assumption moves the motor 2024 completed level by 2.1% and the property levels by ≤ 0.2%. The late-reporting dip of December 2024 (268 losses vs a monthly mean of 385) is carried by G: a row ending 30 Dec 2024 has ages 1-365 and completion 0.74 in motor, which is where the under-reporting of the last month enters (R-0106); no ad-hoc December fix is applied.

Ages observed in this market: 0-730 days, but only January-2023 losses reach 730 and the estimate uses ages up to 540. Not observed: anything beyond 24 months, which is where bodily-injury development lives; that part is borrowed.

## 4. Trend

R-0103 needs at least two mature accident years; the emerging market has one (2023, completion 0.975-0.999), so no trend can be fitted here. The one available step, completed 2024 over completed 2023, is 1.038 (motor), 0.628 (buildings, fire), 0.980 (contents): one noisy observation each, not a trend. Trend is therefore borrowed from the developed market: a log-linear fit of completed burning cost (same completion estimator) on accident years 2021-2023 gives +3.3% (motor), +6.3% (buildings), +5.4% (contents) per year; including 2024 gives −0.5% / +7.8% / +5.0%, the motor change coming from a 2024 completed level that sits below 2023 (549 vs 602), most plausibly because 2024 open claims are reserved low (§6) rather than a real fall.

Adopted: +3% motor, +6% buildings, +5% contents per year, applied through `trend_factor` = (1 + trend)^(2025 − year) on training rows (1.0609 / 1.03 motor; 1.1236 / 1.06 buildings; 1.1025 / 1.05 contents for 2023 / 2024) and 1.0 on test rows. With offset log(exposure × completion / trend_factor) the model estimates the 2025 cost level directly. Sensitivity: ±3 points of annual trend move the 2025 level by about ±4.5% (the training data sit 1.5 years before 2025 on average); a zero trend lowers the predicted level by 4.4% (motor), 8.7% (buildings) and 7.3% (contents). The zero-trend variant is the second candidate under R-0505.

## 5. Large losses

Row targets are capped at the 99th percentile of positive row targets per line (R-0104) and the excess is returned as a line-level multiplier so the total is preserved.

| line | cap (CU) | rows capped | positive rows | excess redistributed | multiplier | share of cost in the top 1% of positive rows |
|---|---|---|---|---|---|---|
| motor | 21,183 | 61 | 6,091 | 1,137,800 | 1.0773 | 15.3% |
| buildings | 142,585 | 11 | 1,011 | 1,024,387 | 1.1200 | 27.1% |
| contents | 21,001 | 10 | 969 | 118,823 | 1.0482 | 12.7% |

Columns: `y_capped` (training rows), flag `dq_flag_large_loss_capped`. The buildings multiplier rests on eleven rows (fire and flood, F-10): computed on 2023 alone it would be about 1.17 and on 2024 alone about 1.06, so the buildings level carries roughly ±5% from the cap year mix alone. The 27 dominant claims identified in profiling are all inside the capped rows.

## 6. Open-claim adequacy (IBNER, R-0105)

Compared: mean incurred of open vs closed claims by accident year and peril, emerging and developed.

- Emerging motor: 2023 open claims (130, almost all bodily injury) average 11,164 vs closed 2,103; 2024 open claims (709) average 4,088 vs closed 1,869. By peril the picture changes: bodily-injury open claims average 11,476 (2023, n=125) and 11,598 (2024, n=135), i.e. the same; the 2024 open own-damage (1,682, n=223) and third-party-property (2,712, n=271) claims are compared with 1-3 open 2023 claims of those perils, which is no comparison. Re-reserving every 2024 open claim at the 2023 open mean of its peril would add 444k = 5.8% to 2024 motor cost, but that number is driven by the uncredible perils.
- Emerging buildings: implied uplift 0.4% of 2024 cost; contents: no 2023 claim is open, nothing to compare.
- Developed (for reference): open 2024 claims average 6,115 (motor) and 14,777 (buildings) against 20-29k for open claims of 2021-2023, the pattern R-0105 describes; whether it is under-reserving or simply that late-surviving open claims are the big ones cannot be separated with these fields.

Decision: no IBNER adjustment applied. Recorded as an uncertainty of 0 to +6% on the motor level and ±1% on property. Local validation on 2024 cannot test it (2024 reserves carry the same bias), so it stays a team decision.

## 7. Resulting target level by line and year

| line | year | exposure | Σ y | raw burning cost (y / exposure) | completion | completed burning cost (y / (exposure × completion)) | at 2025 cost level (× trend_factor) | capped-target level × multiplier (check) |
|---|---|---|---|---|---|---|---|---|
| motor | 2023 | 18,864.5 | 8,162,761 | 432.7 | 0.975 | 443.8 | 470.8 | 443.8 |
| motor | 2024 | 20,104.0 | 7,693,127 | 382.7 | 0.831 | 460.7 | 474.5 | 460.7 |
| buildings | 2023 | 11,372.6 | 5,848,688 | 514.3 | 0.998 | 515.3 | 578.9 | 515.3 |
| buildings | 2024 | 12,095.4 | 3,710,061 | 306.7 | 0.948 | 323.7 | 343.1 | 323.7 |
| contents | 2023 | 14,107.7 | 1,285,655 | 91.1 | 0.9985 | 91.3 | 100.6 | 91.3 |
| contents | 2024 | 14,950.3 | 1,297,700 | 86.8 | 0.970 | 89.5 | 93.9 | 89.5 |

Expected 2025 level before any model (exposure-weighted average of the two trended years): motor ≈ 473 CU per exposure-year, buildings ≈ 455 (2023-heavy because of fire; 343-579 range between the two years), contents ≈ 97. For comparison, the developed market's completed 2023 level is 602 / 434 / 117. check_sub.py prints the raw history (432.7 / 382.7 etc.), so a correct 2025 prediction must sit above the raw 2024 numbers by the completion, trend and new-business effects.

## 8. Known limitations

- One mature accident year: completion shape to 540 days is observed, the tail is borrowed; trend is entirely borrowed; the 2024 completion (0.83 motor) means a sixth of the motor target for 2024 is an assumption.
- Buildings is dominated by fire with 70 claims: the line level moves ±10% between years for reasons the row features are unlikely to explain; the cap multiplier itself rests on eleven rows.
- Open claims are taken at case estimate; a 2024 under-reserving of the size seen in the developed market would understate the motor level by up to ~6%.
- Claims are linked by loss date only; the 36 pre-inception claims are excluded rather than reassigned.
- The target is reported-cost-weighted by completion through the offset; a model with no offset hook must use y/(exposure × completion / trend_factor) with weight (exposure × completion / trend_factor)^(2−p) (R-0304).
- The new-business segment that makes up 76% of 2025 contributes 7% of training exposure; its level is a relativity estimated on 697 / 77 / 102 claims (shift_report §5).
