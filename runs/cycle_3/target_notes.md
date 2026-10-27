# Target construction notes — emerging market

Inputs: `./outputs/cleaned/` tables; outputs: `./outputs/modelling_tables/{motor,buildings,contents}.parquet`.
Scripts: `work/p30_completion.py` (lag curves), `work/p31_modelling_tables.py` (tables and targets),
`work/p32_ibner_trend.py` (IBNER, trend). Valuation date V = 2024-12-31.

## 1. Target definition and reconciliation

For every training row, `y` = Σ over claims linked to the row (loss_date within [period_start,
period_end]) of `incurred_to_date − recoveries`, with repudiated claims contributing 0 (their amounts
are already 0.00). Open claims enter at their case estimate (no IBNER adjustment, §6). `y` is the cost
**reported by the valuation date**, not the ultimate; the ultimate is `y / completion` (§3). Test rows
have `y` null and `completion` 1.0 (the quantity to predict is the ultimate row cost).

| Line | Train rows | Test rows | Σ y | Claims in y | Cap (q99 of y>0) | Rows capped | Cap multiplier |
|---|---|---|---|---|---|---|---|
| motor | 47,283 | 90,521 | 15,855,887.96 | 7,048 | 21,148 | 61 | 1.0775 |
| buildings | 27,447 | 52,295 | 9,558,749.31 | 1,056 | 143,434 | 10 | 1.1188 |
| contents | 34,566 | 66,247 | 2,583,354.30 | 998 | 19,968 | 10 | 1.0526 |
| **total** | 109,296 | 209,063 | **27,997,991.57** | 9,102 | | | |

Reconciliation: cleaned claims table, non-repudiated net incurred = 27,997,991.57; difference 0.00.
Claim count 9,222 in the cleaned table = 9,102 non-repudiated + 120 repudiated. Against the as-delivered
claims (9,258; 28,090,258.83) the movement is exactly the 36 excluded unlinked claims (−92,267.26, F-08).

Column roles in the modelling tables: ids (`row_id, policy_id, customer_id, address_id, period_start,
period_end, split, year`); target/offset (`y, y_capped, n_claims, exposure, completion,
completion_notail, completion_count`); features (unprefixed); `x_*` = excluded from features but kept
for audit and registered re-add tests (`x_customer_since_year, x_campaign_code,
x_customer_service_contacts, x_written_premium, x_renewal_decision, x_start_month, x_row_days` and the
seven `x_<weather>` columns); `dq_*` = data-quality flags, never features (`dq_exposure_class,
dq_exposure_repaired, dq_sum_insured_rescaled, dq_survivor_year, dq_row_has_capped_loss`).
`building_age` (= year − year_built) is derived; `customer_tenure_years` was dropped because it equals
`renewal_count` exactly.

## 2. Claim–policy linkage

Method: join claims to all rows of the same policy_id and keep the row whose period contains the loss
date (inclusive). Match rate 9,222 / 9,258 = 99.6%; no claim matched two rows (the row split at
mid-term changes is contiguous and non-overlapping). The 36 unmatched claims all have loss dates
before the policy's first row (34 before any policy existed) and report lags of 411–565 days,
beyond the 99th percentile of their perils' matched lag distributions; they were excluded, not
re-dated (R-0015), and raised as a team query. Their share of incurred is 0.33% (motor 0.4%,
buildings 0.2%, contents 0.4%), which bounds the level effect of the decision.

## 3. Completion (IBNR)

Why not Part 1's method as written: R-0102 builds the lag curve from the most mature accident years;
this market has two, the older of which is observed to at most 730 days. The substitute (R-0108) is a
**cost-weighted, right-truncation-corrected (reverse-time product-limit) estimate** of the share of
cost reported by lag d, per line, on all 2023–24 claims, which uses each claim only at ages it could
have been observed. Individual claims are capped at 50,000 in the weights so one fire does not shape
the curve; perils are mixed by their natural cost share within the line. The curve is anchored at
540 days (the oldest age at which the risk set is still populated: 1,810 motor, 253 buildings,
253 contents claims observable), and the share beyond 540 days is **borrowed** from the developed
market's own product-limit curve (2021–24 claims, anchored at 1,400 days and assumed complete there).

Row completion = mean of G over the ages at V of the row's days (G(a) = share reported by age a);
`completion_notail` uses the emerging curve alone (nothing after 540 days); `completion_count` is the
unweighted (frequency) version. Test rows: 1.0.

| Line | G(30) | G(90) | G(180) | G(365) | G(540) | G(730) | Borrowed share beyond 540 d | 2023 full-year completion | 2024 full-year completion (spliced / no-tail / developed curve) |
|---|---|---|---|---|---|---|---|---|---|
| motor | 0.600 | 0.756 | 0.851 | 0.935 | 0.977 | 0.992 | 2.3% | 0.970 | **0.804** / 0.823 / 0.816 |
| buildings | 0.867 | 0.938 | 0.971 | 0.993 | 0.998 | 1.000 | 0.2% | 0.998 | **0.941** / 0.943 / 0.926 |
| contents | 0.968 | 0.990 | 0.991 | 0.991 | 1.000 | 1.000 | 0.04% | 0.999 | **0.971** / 0.971 / 0.970 |

Sensitivity of the 2024 full-year completion to the two choices made here (anchor × cap):
motor 0.804 at (540 d, 50k); anchor 365 / 730 d → 0.809 / 0.813; cap 25k / 100k → 0.823 / 0.789
(±2.5% on the 2024 motor ultimate; the cap decides the weight of late-reported bodily-injury claims).
Buildings 0.941, range 0.934–0.947 over the same grid; contents 0.971, range 0.970–0.972.

Observed in this market: ages 1–540 days (body of the curve). Assumed/borrowed: ages 541–1,400 from
the developed market (bodily injury and subsidence are the only perils with mass there; developed
BI reaches 0.978 at 730 days and 0.993 at 1,095), and "complete at 1,400 days". The borrowed share is
2.3% of motor ultimate cost and negligible for property; if the true motor tail were twice the
developed one, 2024 motor completion would be 0.78 instead of 0.80 (+2.9% on the 2024 ultimate level).

Exposure-weighted completion of the training rows actually used (all rows, not just full-year):
motor 2023 0.970 / 2024 0.804; buildings 0.998 / 0.941; contents 0.999 / 0.971. Count completion for
2024: 0.930 / 0.953 / 0.970 — frequency is far more complete than cost because the late-reported
claims are the large bodily-injury ones.

Empirical check (R-0109): 2023 cost reported within 365 days of loss as a share of 2023 cost reported
by V — observed 0.969 (motor), 0.996 (buildings), 0.993 (contents); implied by the spliced curve
0.964 / 0.995 / 0.993 (no-tail 0.969 / 0.996 / 0.993; developed curve 0.966 / 0.992 / 0.995).
Agreement within 0.5 points: the anchor and the borrowed share are consistent with the only direct
test the data allows. Per-peril check: emerging F(365)/F(540) for bodily injury 0.868 vs developed
G(365)/G(540) 0.902 — the emerging BI tail is, if anything, slightly heavier, within sampling error
of 449 claims.

The last calendar month (R-0106): December 2024 losses are at 263 vs a 388 monthly mean; the curve
gives them completion 0.45–0.75 (motor) so the under-reporting is carried by the offset, not by a fix.

## 4. Trend

R-0103 cannot be applied: with two accident years, one of them 80% complete in motor, no trend can be
fitted on this market (the 2024/2023 ultimate ratios are +7% motor, −27% buildings (fire year),
−2% contents — noise and large losses, not trend). Borrowed from the developed market, fitted
log-linear on completion-adjusted burning cost **capped at 50k** for 2021–2023 (completion ≥ 0.97):

| Line | Developed trend 2021–23 | 2021–24 | 2021→22 only | Frequency trend 2021–23 | Assumption for 2025 | Factor to mid-2025 (1.5 yrs from the training midpoint) |
|---|---|---|---|---|---|---|
| motor | −1.3%/yr | 0.0% | +3.7% | −0.6% | **0%** (range −2% to +4%) | 1.000 (0.97–1.06) |
| buildings | +6.4%/yr | +7.3% | +6.3% | +1.7% | **+6%** (range 0% to +8%) | 1.091 (1.00–1.12) |
| contents | +5.1%/yr | +4.7% | +1.5% | +1.9% | **+5%** (range 0% to +7%) | 1.076 (1.00–1.11) |

The training level is the exposure-weighted 2023–24 ultimate (midpoint 1 January 2024); the test
midpoint is 1 July 2025, hence 1.5 years. Two submission candidates are produced (R-0505): with the
borrowed trend and with none; the human chooses. The trend is a borrowed assumption (listed in
adaptation_decisions.md with its level sensitivity: ±9% buildings, ±8% contents, ±5% motor).

## 5. Large losses

Caps at the 99th percentile of positive row targets per line (R-0104): motor 21,148 (61 rows
above it, excess 7.2% of Σy → multiplier 1.0775); buildings 143,434 (10 rows, excess 10.6% → 1.1188);
contents 19,968 (10 rows, 5.0% → 1.0526). Models are trained on `y_capped`; predictions are multiplied
by the line multiplier so the total is preserved. Dominant claims (F-11): 2023 buildings carries ten
fire claims above 125k and 2024 one of 361k (9.7% of its year); the cap therefore moves buildings most.
The capped-vs-raw difference also shows in §7: the 2023 buildings burning cost is 514 raw and 349
capped at 50k.

## 6. Open-claim adequacy (IBNER)

Open claims are a selected sample (large claims close late): in both markets the mean incurred of
open claims is 2–6× that of closed claims of the same year. Like-for-like is only partly possible —
there is one valuation snapshot, so the older year's open claims **at the same age** are not
observable; the developed market at the same valuation date is the substitute.

| | Emerging 2023 | Emerging 2024 | Developed 2023 | Developed 2024 | Developed 2021 (mature) |
|---|---|---|---|---|---|
| motor open share (count / cost) | 3.7% / 17.8% | 20.3% / 37.7% | 3.9% / 25.3% | 21.0% / 36.6% | 1.2% / 6.3% |
| motor BI mean: closed / open | 9,618 / 11,476 | 9,354 / 11,598 | 17,716 / 28,983 | 17,266 / 17,972 | 21,543 / 20,867 |
| buildings open share (count / cost) | 4.0% / 7.5% | 25.3% / 34.7% | 2.9% / 8.2% | 24.7% / 35.5% | 0.3% / 0.7% |
| contents open share (count / cost) | 0 / 0 | 11.6% / 18.0% | 0.3% / 1.4% | 13.2% / 18.4% | 0 / 0 |

Reading: the emerging 2024 open shares are the developed 2024 shares to within a point, so the
reserving stage is the same. In the developed market the mature year's BI mean (21.4k overall for 2021)
is **below** the 2023 case-estimate mean for open BI claims (29.0k), i.e. no sign of under-reserving;
the emerging 2023 and 2024 BI means (10.5k and 11.0k overall) are stable across the two years. **No
IBNER uplift is adopted.** Recorded uncertainty: if 2024 open claims settle at ±10% of their case
estimates, the 2024 level moves ±3.8% (motor), ±3.5% (buildings), ±1.8% (contents); at +20%, +7.5% /
+6.9% / +3.6%. Local validation cannot test this (the 2024 fold carries the same reserves).

## 7. Resulting target level by line and year (per exposure-year)

| Line | Year | Exposure-yrs | Raw burning cost (= Σy / exposure) | Capped-50k raw | Completion | **Ultimate burning cost** (Σy / Σ(exposure×completion)) | Ultimate, capped 50k | After trend to mid-2025 (central) |
|---|---|---|---|---|---|---|---|---|
| motor | 2023 | 18,865 | 433 | 432 | 0.970 | **447** | 446 | 447 |
| motor | 2024 | 20,104 | 383 | 375 | 0.804 | **478** | 467 | 478 |
| buildings | 2023 | 11,373 | 514 | 349 | 0.998 | **515** | 349 | 562 |
| buildings | 2024 | 12,095 | 307 | 242 | 0.941 | **325** | 258 | 355 |
| contents | 2023 | 14,108 | 91 | 91 | 0.999 | **91** | 91 | 98 |
| contents | 2024 | 14,950 | 87 | 87 | 0.971 | **89** | 89 | 96 |

Credibility: motor levels rest on ≈3,500 claims per year (±2–3% sampling error on frequency, more on
cost because of bodily injury); buildings and contents on ≈500 claims per year (±5% frequency, ±15–30%
cost in buildings because fire/flood dominate). The buildings two-year level (≈420 ultimate) is the
least credible number here: the two years differ by 37% on the strength of 28 fire claims.

## 8. Known limitations of the target

- `y` is a reported-at-valuation quantity; the offset `log(exposure × completion)` makes the model
  learn the ultimate, but any mis-specification of the curve shifts the 2024 level directly
  (2024 motor is 80% complete; a ±0.02 error in completion is ±2.5% of level).
- The tail beyond 540 days and completeness at 1,400 days are borrowed (2.3% of motor cost).
- Open-claim case estimates are taken at face value (±4% level uncertainty on motor/buildings).
- 2023 is a survivor sample: its targets describe policies that renewed into 2024; frequency on
  lapsing policies is not represented in that year (2024 contains both).
- Trend to 2025 is not estimable here; it is borrowed with a ±5–9% level range.
- Buildings large-loss experience is two years thin; the cap multiplier (1.119) is estimated from 10 rows.
- The 36 excluded claims (0.33% of cost) would raise levels by that amount if the team decides they
  are genuine late reports rather than date defects.
- Exposure for 1-day rows and the uncovered 31 December 2024 are immaterial (no claims) but are
  conventions of this system, not of the developed one.
