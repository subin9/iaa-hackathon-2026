# Profile of the emerging-market data

Valuation date for claims: 31 December 2024 (both markets). Amounts in CU. All counts below are from the as-delivered tables in `data/emerging/` unless marked *cleaned*. Playbook rule ids (R-xxxx) point at the check that produced the line.

Environment used: Python 3.12.9, polars 1.42.1, pyarrow 24.0.0, pandas 3.0.1, numpy 2.4.3, scikit-learn 1.8.0, lightgbm 4.7.0, jsonschema 4.26.0. Threads limited to 6; seeds fixed at 0/1/2 in the baseline.

## 1. Tables, sizes, keys

| Table | Rows | Cols | Key / grain | Notes |
|---|---:|---:|---|---|
| customers | 135,856 | 17 | customer_id (unique) | one customer per policy per line; a customer can hold policies in 1–3 lines (81,089 / 39,959 / 14,808 customers) |
| addresses | 136,914 | 16 | address_id (unique) | every address is referenced by at least one policy row; a policy can change address mid-term (motor 293, buildings 1,019, contents 1,260 policies) |
| weather | 410,742 | 9 | (address_id, year), years 2023–2025 | exactly 3 rows per address, including the prediction year 2025 |
| claims | 9,258 | 12 | claim_id (unique) | 7,183 motor, 1,059 buildings, 1,016 contents; 11 perils; status closed 8,082 / open 1,056 / repudiated 120 |
| policies_motor | 47,283 | 36 | row_id; 23,722 policies | 2023: 21,680 rows, 2024: 25,603 |
| policies_buildings | 27,447 | 27 | row_id; 14,299 policies | 2023: 12,580, 2024: 14,867 |
| policies_contents | 34,566 | 28 | row_id; 17,689 policies | 2023: 15,834, 2024: 18,732 |
| test_motor | 90,521 | 35 | row_id; 83,907 policies | all 2025; 76.0% new business |
| test_buildings | 52,295 | 26 | row_id; 50,300 policies | all 2025; 75.9% new business |
| test_contents | 66,247 | 27 | row_id; 62,636 policies | all 2025; 76.1% new business |
| sample_submission | 209,063 | 2 | row_id | = 90,521 + 52,295 + 66,247; prediction column all 0 |
| expenses | 8 | 4 | item | developed and emerging loadings side by side; emerging `commission_comparison_site` is null |
| reference_policies | 20 | 50 | row_id | 20 test rows (7/7/6 by line) stacked into one wide schema with a `line` column; purpose undocumented |

Row ids are a line letter plus a global sequence (M…, B…, C…); training ids run 0–109,295 and test ids continue from 109,296, so a row id alone identifies split and line. Policy, customer and address ids are unique within this market only; identical values in `data/developed/` refer to unrelated records and the two markets are never joined.

Link coverage: every policy and test row finds its customer, its address, and a weather row for its year (0 misses in all three). Customer ↔ policy is one-to-one within a line.

## 2. Period structure and years

- Training rows cover policy years 2023 and 2024; test rows cover 2025. Policy terms are 365 days: a full-year 2023 row runs 1 Jan–31 Dec, a full-year 2024 row 1 Jan–**30 Dec** (leap year), a full-year 2025 row 1 Jan–31 Dec. No 2024 row ends on 31 Dec (F-03).
- 78–85% of training rows start on 1 January; 22% of test rows do (the acquired book incepts through the year). Test exposure per row averages 0.87–0.91.
- Rows per policy-year: 1 or 2. A second row follows a `mid_term_change` (motor 3,477 policy-years, buildings 1,041, contents 1,895); in motor the vehicle changes in 99.8% of them, premium always, cover type in 36%. There are no overlaps or gaps between consecutive rows of a policy.
- `renewal_count` increases by exactly 1 per year for every policy, and `new_business` ⇔ `renewal_count == 0` in every table.
- **Persistence (R-0020).** 2023 → 2024: 100% of policies in all three lines; 2023 contains no `cancelled` or `lapsed_by_customer` rows. 2024 → 2025 (test): 84.4–84.7%, with `renewed` → 100% present, `cancelled`/`lapsed` → 0%, but `declined_by_insurer` → 75–95% present. 2023 is therefore a **survivor sample** (F-20) and `declined_by_insurer` is semantically unreliable (F-21).
- 76% of test policies (63,810 motor, 38,197 buildings, 47,714 contents) do not exist in 2024: the broker portfolio taken on at the start of 2025.

## 3. Exposure (R-0001, R-0014)

Convention: inclusive days / 365, rounded to 4 dp (31,197 of 31,198 full-year motor rows with exposure 1.0 span exactly 365 days; every test row matches to 4 dp).

| Table | Rows | Mismatches | Day counts (ratio ≈ 365) | 360-day basis (ratio ≈ 1.0139) | Stored Σ | Σ from dates |
|---|---:|---:|---:|---:|---:|---:|
| policies_motor | 47,283 | 253 | 47 | 206 | 54,429.5 | 38,968.5 |
| policies_buildings | 27,447 | 154 | 33 | 121 | 33,783.1 | 23,468.0 |
| policies_contents | 34,566 | 200 | 34 | 166 | 38,892.9 | 29,058.0 |
| test_motor | 90,521 | 0 | 0 | 0 | 79,006.9 | 79,007.0 |
| test_buildings | 52,295 | 0 | 0 | 0 | 47,376.3 | 47,376.4 |
| test_contents | 66,247 | 0 | 0 | 0 | 59,016.4 | 59,016.5 |

The 114 day-count rows alone inflate stored training exposure by 40%; every burning cost computed on stored exposure is understated by that much. Repaired from dates in all six tables (F-01, F-02). The developed data contain the same defect (5,703 motor rows, max 365), so Part 1 history must also be read on date-derived exposure.

## 4. Amount columns (R-0003, R-0013)

- `written_premium` is annualised (median for rows with exposure < 0.3 equals the full-year median) and clean: motor 193–2,199 (median 502), buildings 63–4,630 (median 238), contents 27–573 (median 119).
- `sum_insured` has a ×1,000 cluster: buildings 53 train + 104 test rows (values to 470m / 568m), contents 57 + 135 rows (to 132m / 98m). On log10(premium ÷ sum insured) the cluster sits 3.0 decades below the main mass with an empty interval of 1.6 decades (buildings) and 2.4 decades (contents); boundary at the midpoint; divided by 1,000 (F-04, F-05). After repair the maxima are 813k / 894k (buildings) and 235k / 283k (contents). Sums insured are rounded to 1,000 (buildings) and 100 (contents) and are indexed about +3% / +2% per year within a policy.
- `voluntary_excess` ∈ {0, 250, 500, 1000}; `compulsory_excess` is constant (250 motor, 350 home) and carries no information (F-24).
- Claim amounts: no unit clusters (log10 incurred is unimodal per line); paid ≤ incurred always, recoveries ≤ incurred always, closed claims have paid = incurred, repudiated claims have all amounts 0. Recoveries occur only on motor own damage (26% of claims, ≈80% of incurred recovered) and motor theft (11%, ≈30%).

## 5. Claims

| Line | Claims | Closed | Open | Repudiated | Net incurred (raw, excl. repudiated) | Loss years |
|---|---:|---:|---:|---:|---:|---|
| motor | 7,183 | 6,236 | 840 | 107 | 15,923,422 | 2021: 4, 2022: 22, 2023: 3,608, 2024: 3,549 |
| buildings | 1,059 | 902 | 157 | 0 | 9,578,176 | 2021: 1, 2022: 2, 2023: 519, 2024: 537 |
| contents | 1,016 | 944 | 59 | 13 | 2,588,661 | 2021: 1, 2022: 4, 2023: 499, 2024: 512 |

- Perils: motor own_damage 2,712, third_party_prop 2,263, glass_hail 1,350, bodily_injury 450, theft 408; buildings storm 466, escape_of_water 268, accidental_damage 122, flood 81, fire 70, subsidence 52; contents theft 418, accidental_damage 340, escape_of_water 172, flood 86. Fire is 70 claims but 45% of buildings incurred; bodily injury is 6% of motor claims and 30% of motor incurred.
- **Linkage (R-0004).** 9,222 claims (99.6%) link to exactly one policy row by policy id and loss date within the row period; 0 link to two rows; 0 claim lines disagree with the row's line. 36 claims link to none: all have a loss date before the policy's first row (2021-10 to 2023-01) and report lags of 411–565 days against a matched-claim 99.5% lag of 334 days (R-0015) → excluded, 92,267 CU = 0.33% of incurred, team query (F-06).
- **Duplicates (R-0002):** none on the full content key; 4 pairs share policy and loss date with different perils (one accident, two perils) (F-07).
- **Valuation (R-0007):** latest loss 2024-12-29, latest report 2024-12-30, nothing in 2025. Report lag median 8 d, p90 37 d, p99 317 d; by peril bodily injury median 99 d / p90 318 d, subsidence 56 / 186 d, everything else median ≤ 14 d. December 2024 has 268 claims against 330–420 in other 2024 months, concentrated in third-party and bodily injury (F-09). Open share: 2023 0–4%, 2024 11–25% by line.
- **Large losses (R-0008):** 10 buildings fire claims of 125k–361k CU each exceed 2% of their year; the largest is 9.7% of 2024 buildings incurred. Top 1% of claims carry 16% / 26% / 13% of net incurred (motor / buildings / contents) (F-10).

## 6. Distributions and missingness

- Age is banded (`17-24, 25-34, 35-49, 50-64, 65+`); the U-shaped band mix (65+ 28%, 17-24 20%) is also what the developed market's integer ages produce when banded (65+ 31%, 17-24 14%). Claim frequency by band is 0.280 / 0.195 / 0.142 / 0.132 / 0.164, consistent with the labels; `years_licensed` and `marketing_segment` (young/midlife/mature/senior) agree with the band on every row.
- Categorical code lists are identical in training and test for every column; `make_model` has 300 levels (136–207 rows each in training), `previous_insurer` 40, `branch_id` 25, `marketing_segment` 12, `email_domain` 5.
- `occupation` has 81 raw levels around a 20-value code list: case and trailing-space variants plus a "Self-employed " prefix at a uniform 10% in every base occupation including retired/student/unemployed → random corruption, stripped (F-16, R-0021).
- **Missingness (R-0018).** Fourteen columns are null on 11.8–12.3% of rows each (customers: occupation, marital_status, household_size, years_at_address; addresses: distance_to_river_km, soil_type, roof_type, energy_rating; motor: vehicle_age, engine_size_cc, overnight_parking; buildings: days_unoccupied, smoke_alarms; contents: security_level, high_value_items). Rates are identical in train and test and across join cohorts; co-missingness equals the marginal rate; null and non-null rows match on every other covariate (standardised differences < 0.04) and on claim frequency and burning cost; within multi-row policies the null hits one row at the chance rate. Treated as independent draws (F-17); the policy-stable attributes are reconstructed from sibling rows of the same policy (F-18; training nulls fall to ≈1%, test nulls to the new-business share). `flood_zone` nulls (2.9%) are different: closer to rivers, lower, and with higher buildings claim frequency → kept as an "unknown" level (F-19). The developed market has 2.5% nulls on the same columns.
- Weather: 2025 values exist for every address and differ from 2024 at every address; the 2025 means move materially (freezing days 17.5 → 28.9, rainfall 1,375 → 1,251 mm, hail 17.1 → 11.4 days). Address-level year-to-year correlation is 0.2 for hail and 0.9 for rainfall (F-15, R-0022).

## 7. Leakage and time-identity checks (R-0005, R-0006, R-0016, R-0019, R-0022)

| Column | Evidence | Decision |
|---|---|---|
| customer_since_year | deterministic function of first policy year (2025 ⇔ test); single-feature adversarial AUC 0.88 | excluded; `tenure_years` derived |
| campaign_code | null ⇔ customer_since_year ≤ 2022; null-indicator AUC 0.79 | excluded |
| customer_service_contacts | 0 contacts ⇒ 0 claims; 1 ⇒ 0.04, 2 ⇒ 0.25, 4+ ⇒ 1.18 claims/yr; tail only in training | excluded |
| renewal_decision | end-of-period outcome, absent from test | excluded |
| missed_payments_12m | same distribution in test; prior-year value predicts next-year frequency as well as same-year value | kept |
| new_business, renewal_count, tenure_years | shift because the test book is 76% new business; meaning unchanged (R-0019) | kept as mix features; evaluate on the new-business subset |
| weather (yearly) | prediction-year values are a year effect (per-index AUC 0.55–0.75) | yearly values excluded; optional address mean over 2023–24 kept as a flagged optional group |

Multivariate adversarial AUC (2024 train vs 2025 test): 1.00 with all columns; 0.82 after removing the two stamps (driven by new_business / renewal_count = mix); 0.63 (motor) and 0.56 (home) after also removing the new-business indicators — the residual is portfolio mix (younger drivers, higher-cardinality mix in make_model / occupation / previous_insurer) and is what the shift report explains.

## 8. Structural differences from the developed data

- Columns only in developed: `customers.date_of_birth`, `customers.credit_band`; motor `driver_age`, `annual_mileage`, `telematics_opt_in`, `telematics_score`; home `policyholder_age`. Only in emerging: `customers.gender`; `driver_age_band`, `policyholder_age_band`. The emerging market records age only as a 5-level band and has no credit score, mileage or telematics.
- Same name, different encoding: `construction_type` (developed free-text/mixed-case `brick/stone/non_standard/W/T`; emerging codes `BRK/STN/MIX/WOD`), `region` (R01–R12 vs E01–E06, different geographies, not mappable), `occupation` (clean 20-level list vs noisy 81 raw levels). `campaign_code` exists in both but its null boundary differs (developed: joined ≤ 2020; emerging: ≤ 2022).
- Scale: developed has 4 policy years (2021–2024), ≈980k / 708k / 722k training rows and 163k claims; emerging has 2 years, 47k / 27k / 35k rows and 9.3k claims — 17× fewer claims, 1,059 buildings claims in total.
- Same defects exist in both (day-count exposures, ×1,000 sums insured at 0.2% of rows), but the emerging null rate is 5× higher and the free-text noise is new.
- Weather climate differs: emerging is warmer (15–16 °C vs 12–13 °C), wetter (1,375 vs 1,000 mm), with 2–3× the hail days, half the freezing days and 3× the wildfire index.
- Extra emerging tables: `expenses` (loadings for both markets, one null) and `reference_policies`.

## 9. Reconciliation (links 1–3 of the ladder, R-0012/R-0017)

| Link | Raw | Cleaned | Explained by |
|---|---:|---:|---|
| Rows, every policy/test table | unchanged | unchanged | no row removed (F-01…F-05, F-18 repair in place) |
| Exposure, training (motor / buildings / contents) | 54,429.5 / 33,783.1 / 38,892.9 | 38,968.5 / 23,468.0 / 29,058.0 | F-01 (114 day-count rows), F-02 (493 rows on 360-day basis) |
| Exposure, test | 79,006.9 / 47,376.3 / 59,016.4 | identical | no mismatches |
| Claims rows | 9,258 | 9,222 | F-06 (36 unlinked pre-inception claims); F-07 (0 duplicates) |
| Net incurred excl. repudiated | 28,090,258.83 | 27,997,991.57 | F-06: 92,267.26 (0.33%) |
| Σ y in modelling tables vs cleaned claims | — | 27,997,991.57 = 27,997,991.57 | exact, by line (15,855,887.96 / 9,558,749.31 / 2,583,354.30) |

Pipeline: `work/c01_clean.py` (cleaning, prints links 1–2), `work/c02_targets.py` (targets, prints link 3), `work/c03_findings.py` (findings.json from the recorded statistics).
