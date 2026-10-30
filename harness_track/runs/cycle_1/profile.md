# Emerging-market data profile

Scope: the thirteen tables in `./data/emerging/` (read-only), profiled as delivered and after the treatments recorded in `findings.json` and written to `./outputs/cleaned/`. The developed market (`./data/developed/`) is used for structural comparison only; no developed table was joined to an emerging table. Amounts are CU. Claims are valued at 31 December 2024.

Environment: Python 3.12.9, polars 1.42.1, pyarrow 24.0.0, pandas 3.0.1, numpy 2.4.3, scikit-learn 1.8.0, lightgbm 4.7.0, jsonschema 4.26.0. Threads capped at 6; seeds fixed at 0 wherever randomness is used. Scripts: `work/p0*_*.py` (profiling), `work/p10_clean.py` (cleaning), `work/p11_findings.py` (findings).

## 1. Tables, sizes and keys

| table | rows | cols | key | notes |
|---|---|---|---|---|
| customers | 135,856 | 17 | customer_id (unique) | one row per customer; 36,768 customers appear in training rows, 130,226 in test rows, 31,138 in both |
| addresses | 136,914 | 16 | address_id (unique) | every address is used by at least one policy row |
| weather | 410,742 | 9 | (address_id, year) | exactly 3 rows per address: 2023, 2024 and 2025 (the prediction year) |
| policies_motor | 47,283 | 36 | row_id (unique) | 23,722 policies, 2023-2024 |
| policies_buildings | 27,447 | 27 | row_id | 14,299 policies |
| policies_contents | 34,566 | 28 | row_id | 17,689 policies |
| claims | 9,258 | 12 | claim_id (unique) | motor 7,183, buildings 1,059, contents 1,016 |
| test_motor | 90,521 | 35 | row_id | 83,907 policies, all periods inside 2025; no renewal_decision column |
| test_buildings | 52,295 | 26 | row_id | 50,300 policies |
| test_contents | 66,247 | 27 | row_id | 62,636 policies |
| sample_submission | 209,063 | 2 | row_id | = 90,521 + 52,295 + 66,247; prediction column all zero |
| expenses | 8 | 4 | item | expense and loading assumptions, developed vs emerging |
| reference_policies | 20 | 50 | row_id | 20 exact copies of test rows (7 motor, 7 buildings, 6 contents; 18 new business) in a wide combined schema |

Links. Every `customer_id` and `address_id` on every policy, test and reference row resolves to the customers and addresses tables (100%). Every claim's `policy_id` exists in the policy table of the claim's line (the first letter of policy_id, M/B/C, matches `line` on all 9,258 claims). Within a line each customer holds exactly one policy; across lines 21,900 training customers hold one line, 10,794 two and 4,074 all three, so customer-level pooling across lines is possible. Addresses are shared by several motor policies (up to 10 per address, i.e. several customers at one address). Weather joins to addresses on (address_id, year) with no gaps and no duplicates.

## 2. Time structure

- Training rows: period_start 2023-01-01 to 2024-12-29, period_end 2023-01-02 to 2024-12-30. Test rows: 2025-01-01 to 2025-12-31. No row spans a calendar year; no two rows of a policy overlap; consecutive rows of a policy have no gaps (a mid-term change splits the year into adjacent rows). Rows per policy in training: 1 (14%), 2 (73%), 3 (12%), 4 (<1%); in test 1 or 2.
- Convention: exposure = (period_end − period_start + 1)/365 to 4 decimals. A full 2023 year is 1 Jan-31 Dec (365 days). A full 2024 year is booked 1 Jan-30 Dec (365 days, exposure 1.0), so no annual 2024 row covers 31 Dec 2024 (finding F-23). Full 2025 rows run 1 Jan-31 Dec.
- Renewal chain: `renewal_count` rises by exactly 1 from a policy's 2023 row to its 2024 row and from its 2024 row to its 2025 test row for every policy; `renewal_count` equals period_year − `customer_since_year` on every training and test row; `new_business` is true exactly when `customer_since_year` equals the period year. Hence tenure is fully recorded by `renewal_count`, and `customer_since_year` is a pure calendar stamp (F-14).
- Policies with rows in both training years: motor 20,084 of 23,722, buildings 12,107 of 14,299, contents 14,982 of 17,689; the remainder started in 2024.
- Claims: loss_date 2021-10-27 to 2024-12-29 as delivered (2023-01-01 to 2024-12-29 after cleaning), report_date 2023-01-02 to 2024-12-30. No claim has a loss in 2025. Report lag: median 8 days; 90th percentile 41 (motor), 31 (buildings), 22 (contents) days; 99th percentile 330 / 179 / 73 days; maximum 653.

## 3. Portfolio by line and year (cleaned exposure)

| line | year | rows | policies | exposure (years) | new-business share | claims (excl. repudiated) | frequency | severity (net) | raw burning cost | open share |
|---|---|---|---|---|---|---|---|---|---|---|
| motor | 2023 | 21,680 | 20,084 | 18,864.5 | 12.1% | 3,557 | 0.189 | 2,295 | 432.7 | 3.7% |
| motor | 2024 | 25,603 | 23,722 | 20,104.0 | 15.3% | 3,491 | 0.174 | 2,204 | 382.7 | 20.3% |
| motor | 2025 (test) | 90,521 | 83,907 | 79,006.9 | 76.0% | | | | | |
| buildings | 2023 | 12,580 | 12,107 | 11,372.6 | 12.0% | 519 | 0.0456 | 11,269 | 514.3 | 4.0% |
| buildings | 2024 | 14,867 | 14,299 | 12,095.4 | 15.3% | 537 | 0.0444 | 6,909 | 306.7 | 25.3% |
| buildings | 2025 (test) | 52,295 | 50,300 | 47,376.3 | 75.9% | | | | | |
| contents | 2023 | 15,834 | 14,982 | 14,107.7 | 11.7% | 491 | 0.0348 | 2,618 | 91.1 | 0.0% |
| contents | 2024 | 18,732 | 17,689 | 14,950.3 | 15.3% | 507 | 0.0339 | 2,560 | 86.8 | 11.6% |
| contents | 2025 (test) | 66,247 | 62,636 | 59,016.4 | 76.1% | | | | | |

2024 is incomplete at the valuation date (open shares above, December 2024 losses 268 against a 2023 monthly mean of 385), so 2024 frequency and severity are understated; the target construction corrects this. The 2023 buildings burning cost is 68% above 2024 because of fire: 49 fire claims costing 3.22m in 2023 against 21 costing 1.13m in 2024 (fire is 45% of buildings cost over the two years, F-10); storm and escape-of-water cost per exposure-year are flat to rising between the years. Even without the top 1% of claims, 2024 buildings cost per exposure-year is about a quarter below 2023, so the fire frequency itself, not only a few large claims, drives the difference.

The 2025 test year is roughly 3.9x the 2024 exposure in every line and three quarters of it is new business taken on from a broker: 68,823 motor, 39,716 buildings and 50,441 contents test rows belong to policies never seen in training; the remaining 21,698 / 12,579 / 15,806 rows are renewals of 2024 training policies (every test policy that is not new business is in the training data). Training contains 6,535 / 3,786 / 4,716 new-business rows (3,040 / 1,810 / 2,233 exposure-years) on which any new-business effect has to be learned.

## 4. Distributions of the main risk factors (training rows unless stated)

- Ages are banded in five bands, not recorded as integers. Training mix (all lines within 1 pt): 17-24 20%, 25-34 19%, 35-49 16%, 50-64 17%, 65+ 28%. Test mix: 25%, 25%, 13%, 13%, 24%, i.e. the test book is younger; the training new-business rows have almost the test mix (29%, 26%, 12%, 13%, 21%).
- Channel: broker 70%, direct 25%, comparison_site 5% in every line, training and test alike. `discount_applied` is a function of channel (direct 0.05, broker 0, comparison_site 0 or 0.10); the 0.10 share of comparison-site rows rises from 14% (train) to 77% (test).
- Payment: annual 55%, monthly 45%. Voluntary excess 0 / 250 / 500 / 1000 at 40/30/20/10% (motor) and 50/30/15/5% (property). Compulsory excess is constant per line (250 motor, 350 property) and carries no information.
- Motor: comprehensive 79%, third-party fire & theft 11%, third-party only 10%; hatchback 40%; manual 55%; petrol 54%, diesel 30%, hybrid 15%, electric 2%; vehicle_age median 9 years (minimum 3, maximum 26); engine size median 2,100 cc; vehicle_value_group 1-20, median 11; 300 make_model codes, each 0.2-0.4% of rows; ncb_years 0-15 with a mode at 1-2; years_licensed 0-73 (median 24). ncb_years exceeds years_licensed on 16% of training rows and 22% of test rows, concentrated in the two youngest bands (F-18).
- Buildings: sum_insured median 229k (p5 100k, p95 413k) after rescaling (F-03); construction BRK 70%, WOD 12%, MIX 10%, STN 8%; owner-occupied 90%; days_unoccupied median 7; smoke alarms 85% where recorded; written premium median 238 with a continuous right tail to 4,630.
- Contents: sum_insured median 35.8k (p5 14k, p95 83k) after rescaling (F-04); owners 57%, renters 43%; security standard / locks / alarm_and_locks about one third each where recorded; high_value_items 0-5, 44% zero.
- Customers: gender F/M 50/50; occupation 20 base occupations plus a self-employed variant of each (10% of customers) after normalisation (F-11), 'Retired' 14% and 'Student' 7% the largest; marital status single 40%, married 38%; household size median 2; prior_claims_5y mean 0.27 (77% zero) with the same mean in every segment and in the test book; licence_points 0/3/6/9 at 80/12/6/2%; marketing_segment young_affluent 26% (test 29%); previous_insurer 40 codes of 2.5% each; branch_id 25 branches of 4% each.
- Addresses: six regions E01-E06 (E03 29%, E06 20%, E02 18%, E05 16%, E01 13%, E04 4%); suburban 45%, urban 25%, rural 20%, dense urban 10%; flood_zone 1-5 (69% zone 1); elevation 0-60 m (median 7.5 m, a low-lying market compared with 0-197 m in the developed market); year_built 1862-2021; property type semi-detached 30%, detached 25%, terraced 25%, flat 20%.
- Written premium is an annual rate, not pro-rated: it does not vary with exposure (correlation −0.03) and differs between the rows of a mid-term-changed policy year.

## 5. Missingness

Fifteen columns carry ~12% nulls (11.8-12.3%) in training and test alike: customers.occupation, marital_status, household_size, years_at_address; addresses.distance_to_river_km, soil_type, roof_type, energy_rating; motor vehicle_age, engine_size_cc, overnight_parking; buildings days_unoccupied, smoke_alarms; contents security_level, high_value_items. The number of nulls per row follows the binomial distribution expected from independent 12% draws, and null rates do not differ by year, new-business flag or claim outcome, so the mechanism is missing-completely-at-random (F-12); the developed market has 2.5% in the same columns. Two columns differ: addresses.flood_zone is null on 2.95% of addresses and those addresses are lower and closer to rivers than average (missing-not-at-random, F-13); customers.campaign_code is null for every customer who joined before 2023 and populated for every customer who joined in 2023-2025 (a cohort marker, see shift report). In claims, repairer_id is populated only for motor (69% of motor claims) and third_party_id only for bodily-injury and third-party-property claims (100% of those).

## 6. Claims

- 9,258 claims as delivered: closed 8,082, open 1,056, repudiated 120. Repudiated claims have zero paid and zero incurred. Paid never exceeds incurred; closed claims have paid = incurred; recoveries never exceed incurred and occur only on motor own_damage (26% of those claims) and theft (11%); report_date ≥ loss_date everywhere (F-08).
- Perils by line (count share, cost share after cleaning): motor own_damage 38% / 19%, third_party_prop 31% / 34%, glass_hail 19% / 6%, bodily_injury 6% / 30%, theft 6% / 10%; buildings storm 44% / 13%, escape_of_water 25% / 11%, accidental_damage 12% / 1%, flood 8% / 22%, fire 7% / 45%, subsidence 5% / 8%; contents theft 41% / 47%, accidental_damage 34% / 8%, escape_of_water 17% / 14%, flood 9% / 31%.
- Claim counts are thin for property: about 520 buildings and 500 contents claims per accident year, 70 fire claims and 52 subsidence claims in total. Fire alone is 45% of buildings cost; the largest fire is 9.7% of 2024 buildings cost and the eleven claims above 2% of their year total are 30% of 2023 buildings cost (F-10). Motor is credible by count (3,500 claims a year) but bodily injury (449 claims) carries 30% of motor cost.
- Linkage: 9,222 claims (99.6%) link by loss_date to exactly one policy row of the same line; the 36 others have loss dates 14-431 days before the policy's first row and report lags of 411-565 days and were excluded (F-07).
- Valuation: latest loss 2024-12-29, latest report 2024-12-30, nothing in 2025 (F-09). Cost-weighted reporting of the 2023 accident year: 60% of motor cost reported within 30 days, 77% within 90, 96% within 365; buildings 91% / 95% / 99.7%; contents 96% / 99% / 99%.

## 7. Treatments and reconciliation (R-0012)

| table | rows in | rows out | what changed |
|---|---|---|---|
| policies_motor | 47,283 | 47,283 | exposure recomputed from dates on all rows; 253 rows changed beyond rounding (47 day counts, 206 on a 360-day basis); exposure total 54,429.5 → 38,968.5 |
| policies_buildings | 27,447 | 27,447 | 154 exposure rows changed (33 day counts, 121 360-basis); total 33,783.1 → 23,468.0; sum_insured ÷1000 on 53 rows |
| policies_contents | 34,566 | 34,566 | 200 exposure rows changed (34 day counts, 166 360-basis); total 38,892.9 → 29,058.0; sum_insured ÷1000 on 57 rows |
| test_motor | 90,521 | 90,521 | exposure recomputed, no value changed |
| test_buildings | 52,295 | 52,295 | exposure unchanged; sum_insured ÷1000 on 104 rows |
| test_contents | 66,247 | 66,247 | exposure unchanged; sum_insured ÷1000 on 135 rows |
| reference_policies | 20 | 20 | same two treatments applied; nothing changed |
| customers | 135,856 | 135,856 | occupation normalised on 47,924 rows (80 → 40 distinct non-null values) |
| claims | 9,258 | 9,222 | 36 pre-inception claims removed (F-07) |
| addresses, weather, expenses, sample_submission | unchanged | unchanged | copied through |

Claims reconciliation: count 9,258 → 9,222 (−36, all F-07). Net incurred excluding repudiated claims 28,090,258.83 → 27,997,991.57 (−92,267.26, the net incurred of the 36 removed claims; −0.33%). Repudiated claims 120 → 120. No amount on any remaining claim was changed. Cleaned tables carry the as-delivered columns with identical types plus boolean flags `dq_flag_exposure_repaired`, `dq_flag_sum_insured_rescaled` (policy, test and reference tables) and `dq_flag_occupation_normalised` (customers); these are audit markers, not risk factors (R-0011).

Checks that found nothing: no duplicate claims on content keys (F-06); no unit clusters in premiums, excesses or claim amounts (F-05); no exposure defect in any test file; no orphan customer, address or policy identifiers; no overlapping or gapped policy rows.

## 8. Structural differences from the developed market

| aspect | developed (Part 1) | emerging (Part 2) |
|---|---|---|
| history | 4 accident years 2021-2024, 163,150 claims | 2 accident years 2023-2024, 9,222 usable claims |
| volume | 980k / 708k / 722k training rows; test 255k / 184k / 187k | 47k / 27k / 35k training rows; test 91k / 52k / 66k |
| test composition | 15% new business | 76% new business (acquired broker book), test 3.9x the 2024 exposure |
| age | integer `driver_age` / `policyholder_age` (17-91) | five bands `driver_age_band` / `policyholder_age_band` |
| customer columns | `date_of_birth`, `credit_band` present; no gender | `gender` present; no date of birth, no credit band |
| motor columns | `annual_mileage`, `telematics_opt_in`, `telematics_score` | absent |
| occupation | 20 clean values | 80 raw strings = 20 values × casing/whitespace variants + 'Self-employed ' prefix |
| construction_type | 11 raw codes (Brick/brick/BRICK, stone/STONE, W/w, T/t, non_standard/NON_STANDARD) | 4 codes BRK, STN, WOD, MIX |
| region | R01-R12 | E01-E06 (different geography, no correspondence) |
| elevation | 0-197 m | 0-60 m |
| missingness | 2.5% in the optional columns | ~12% in the same columns |
| channel mix | direct 40%, comparison_site 35%, broker 25% | broker 70%, direct 25%, comparison_site 5% |
| extra tables | none | expenses (loadings), reference_policies (20 worked examples) |
| customers linkage | 10% of developed motor policy rows reference a customer_id absent from developed customers | 100% resolve |
| claims behaviour | motor frequency 0.14-0.15, severity 3,900-4,200; buildings 0.044-0.046, 8,700-10,300; contents 0.040, 2,660-2,930 | motor 0.17-0.19, 2,200-2,300; buildings 0.044-0.046, 6,900-11,300; contents 0.034-0.035, 2,560-2,620 |
| reporting speed (cost within 365 days, mature years) | motor 93%, buildings 99%, contents 99% | motor 96%, buildings 99.7%, contents 99% |

The same operational conventions appear in both markets: 365-day annual periods ending 30 Dec in the leap year, day-count exposure errors (5,489 developed motor rows), identical peril and status vocabularies, pre-inception claims with long report lags (414 in developed), compulsory excess constant per line.

## 9. Other tables

- expenses: fixed expense 85 CU per policy (developed 45), variable expense 15% (12%), broker commission 20% (15%), direct 0%, comparison-site commission null for emerging although 5% of policies use that channel (F-19), premium tax 8% (12%), catastrophe reinsurance 12% of property risk premium (6%), target margin 8% (5%). These feed a premium build, not the risk-cost target.
- reference_policies: the 20 rows are the team's worked examples; they are present in the cleaned folder with the test treatments applied (F-22).
- weather: year-level means move materially between years (hail days 14.0 / 17.1 / 11.4 in 2023 / 2024 / 2025; freezing days 21 / 17 / 29; rainfall 1,381 / 1,375 / 1,251 mm), so 2025 values are both unknowable at pricing time and different from the training years (F-17).
