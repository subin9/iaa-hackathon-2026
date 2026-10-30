# Profile of the emerging-market data

Scope: `./data/emerging/` as delivered (read-only), profiled with the data-readiness playbook. Claims are valued at
31 December 2024. Amounts in CU. Where a number refers to the cleaned tables it says so; the treatments themselves are
in `findings.json` and the cleaned tables in `outputs/cleaned/`.

Environment: Python 3.12.9, polars 1.42.1, pyarrow 24.0.0, pandas 3.0.1, numpy 2.4.3, scikit-learn 1.8.0,
lightgbm 4.7.0, jsonschema 4.26.0; Windows 11; ≤ 6 threads; seeds fixed (0 for sampling, 11/22/33 for models).
Scripts: `work/p0*` profiling, `work/p10_clean.py` cleaning, `work/p11_findings.py` findings, `work/p20_shift.py`
shift statistics, `work/p30_target.py` targets, `work/p40_baseline.py` baseline.

## 1. Tables, sizes, keys

| Table | Rows | Columns | Key | Years |
|---|---|---|---|---|
| policies_motor | 47,283 | 36 | row_id (unique); policy_id 23,722 | 2023–2024 |
| policies_buildings | 27,447 | 27 | policy_id 14,299 | 2023–2024 |
| policies_contents | 34,566 | 28 | policy_id 17,689 | 2023–2024 |
| test_motor | 90,521 | 35 | policy_id 83,907 | 2025 |
| test_buildings | 52,295 | 26 | policy_id 50,300 | 2025 |
| test_contents | 66,247 | 27 | policy_id 62,636 | 2025 |
| claims | 9,258 (9,222 cleaned) | 12 | claim_id unique; policy_id 7,416 | loss 2021-10 … 2024-12; report 2023-01 … 2024-12 |
| customers | 135,856 | 17 | customer_id unique | customer_since_year 2008–2025 |
| addresses | 136,914 | 16 | address_id unique | — |
| weather | 410,742 | 9 | (address_id, year): 136,914 × {2023, 2024, 2025} | 2023–2025 |
| expenses | 8 | 4 | item | — |
| reference_policies | 20 | 50 | row_id (= 20 test row_ids) | 2025 |
| sample_submission | 209,063 | 2 | row_id = union of the three test files | 2025 |

Test files lack only `renewal_decision` relative to the policy tables (as in the developed market).
`sample_submission` has 90,521 + 52,295 + 66,247 = 209,063 rows, all predictions 0.

## 2. Policy tables (training years)

**Row convention.** Rows are calendar-year slices of a policy: no row crosses a year end; a policy has one row per year,
or two when a mid-term change occurred (the second row carries the new vehicle for motor, a new address for
buildings in 100% of pairs, a new address or sum insured for contents). 2024 rows end on 2024-12-30, 2023 rows on
12-31 (365 covered days in each year; no claim falls on 30/31 December 2024). Consecutive rows of a policy are
contiguous (gap of exactly one day). Stored `exposure` is inclusive days ÷ 365 on 99.3% of rows; the rest are a
day-count cluster (114 rows) and a 360-day-basis cluster (494 rows), both repaired (F-EXP-DAYS, F-EXP-360).

| Line | Year | Rows | Policies | Exposure (cleaned, years) | New-business rows | Broker share | Two-row policy-years |
|---|---|---|---|---|---|---|---|
| motor | 2023 | 21,680 | 20,084 | 18,865 | 12.1% | 70.1% | 3,477 (both years) |
| motor | 2024 | 25,603 | 23,722 | 20,104 | 15.3% | 70.1% | |
| buildings | 2023 | 12,580 | 12,107 | 11,373 | 12.0% | 70.2% | 1,041 |
| buildings | 2024 | 14,867 | 14,299 | 12,095 | 15.3% | 70.3% | |
| contents | 2023 | 15,834 | 14,982 | 14,108 | 11.7% | 70.3% | 1,895 |
| contents | 2024 | 18,732 | 17,689 | 14,950 | 15.3% | 70.3% | |

Raw stored exposure summed to 54,430 (motor), 33,783 (buildings), 38,893 (contents) exposure-years because of the
day-count rows; cleaned sums are 38,969 / 23,468 / 29,058.

**Persistence.** Every 2023 policy reappears in 2024 (100%) and no 2023 row is marked lapsed or cancelled; 85% of
2024 policies reappear in the 2025 test files (motor 20,097 of 23,722; buildings 12,103 of 14,299; contents 14,922 of
17,689). The 2023 year is therefore a survivor sample (F-SURVIVOR-2023).

**Distributions (motor).** driver_age_band 65+ 28%, 17-24 20%, 25-34 19%, 50-64 17%, 35-49 16%; years_licensed is
consistent with the band (17-24 never above 7). ncb_years 0–15 with a mass at 1–2 and at 10–15; it exceeds
years_licensed on 16% of rows (F-NCB-GT-LICENCE). vehicle_value_group 1–20 (mode 11); vehicle_age 3–27 (median 9);
engine_size_cc 500–3,600; body_type hatchback 40%; fuel petrol 54% / diesel 30% / hybrid 15% / electric 2%;
cover comprehensive 79%; overnight_parking driveway 44% / street 27% / garage 17% / null 12%; vehicle_use social
45% / commuting 45% / business 10%; named_young_driver 5%; voluntary_excess 0 / 250 / 500 / 1000 (40/30/19/10%);
compulsory_excess constant 250; channel broker 70% / direct 25% / comparison_site 5%; payment annual 55%;
missed_payments_12m 0 on 92%; written_premium median 502 (p1 273, p99 1,582); renewal_count 0–16 (0 = new
business exactly); customer_service_contacts 0 on 58%, max 20 (training-only tail, leakage: F-LEAK-CONTACTS);
discount_applied is a function of channel × new_business (F-REDUNDANT-DISCOUNT); renewal_decision renewed 85%,
mid_term_change 7%, lapsed 5%, cancelled 3%, declined_by_insurer 0.5% (post-period outcome: F-LEAK-RENEWAL-DECISION).

**Buildings.** sum_insured (cleaned) p1 73,000, median 229,000, p99 509,000, max 813,000 (53 rows were ×1,000:
F-SI-UNIT); construction BRK 70% / WOD 12% / MIX 10% / STN 8%; occupancy owner 90%; days_unoccupied median 7
(null 12%); smoke_alarms true 75% (null 12%); mortgage 55%; accidental_damage_cover 40%; compulsory_excess 350;
written_premium median 238 (p99 2,199).

**Contents.** sum_insured (cleaned) p1 10,300, median 35,800, p99 111,900, max 235,000 (57 rows ×1,000);
tenure owner 57%; security_level standard / alarm_and_locks / locks ≈ 31/31/27%, null 12%; high_value_items 0–5
(null 12%); works_from_home 25%; lodgers 5%; bicycle_cover 15%; written_premium median 119 (p99 298).

## 3. Test tables (2025)

| Line | Rows | Policies | Exposure | New business (rows / exposure) | Also in training | Broker |
|---|---|---|---|---|---|---|
| motor | 90,521 | 83,907 | 79,007 | 76.0% / 76.9% | 20,097 policies | 70% |
| buildings | 52,295 | 50,300 | 47,376 | 75.9% / 76.8% | 12,103 | 70% |
| contents | 66,247 | 62,636 | 59,016 | 76.1% / 77.0% | 14,922 | 70% |

New-business rows incept almost entirely in January 2025 (motor: 60,769 of 68,823; the remaining 8,000 spread evenly
over February–December), i.e. the acquired broker book is transferred in one block; renewal rows start on 1 January
(93–96%). Mean exposure 0.88–0.92 for new business, 0.84–0.88 for renewals; two-row policy-years exist in test as well
(motor 6,614). Test customers: 130,226, of whom 99,088 are new to the customers table and all carry
`customer_since_year = 2025`. The test age mix is younger (17-24 and 25-34 each 25% of exposure vs 19–20% in
training; 65+ 24% vs 29%). All stored test exposures equal inclusive days ÷ 365 exactly; 104 buildings and 135
contents test rows carry the ×1,000 sum insured defect and were repaired identically.

## 4. Claims

| Line | Raw claims | Cleaned | Linked to a row | Repudiated | Incurred (cleaned) | Recoveries | Open 2023 / 2024 |
|---|---|---|---|---|---|---|---|
| motor | 7,183 | 7,155 | 7,155 | 107 | 16.76 M | 0.90 M (own_damage 26% of claims, theft 5%) | 130 / 709 |
| buildings | 1,059 | 1,056 | 1,056 | 0 | 9.56 M | 0 | 21 / 136 |
| contents | 1,016 | 1,011 | 1,011 | 13 | 2.58 M | 0 | 0 / 59 |

Claims by accident year (cleaned): motor 2023 3,606 (3,427 closed, 130 open, 49 repudiated), 2024 3,549 (2,782 /
709 / 58); buildings 519 (498 / 21) and 537 (401 / 136); contents 499 (491 / 0 / 8) and 512 (448 / 59 / 5).
36 raw claims had loss dates in 2021–2023 before any period of their policy (F-CLM-PREINCEPT, excluded, 0.3% of
incurred). No content-key duplicates (F-CLM-DUP). Repudiated claims carry zero paid, incurred and recoveries.
paid ≤ incurred always; closed claims have paid = incurred; recoveries never exceed incurred.

Perils (cleaned, share of claims / of net cost): motor own_damage 38% / 19%, third_party_prop 31% / 34%, glass_hail
19% / 7%, bodily_injury 6% / 30%, theft 6% / 10%; buildings storm 44% / 13%, escape_of_water 25% / 11%,
accidental_damage 12% / 1%, flood 8% / 22%, fire 7% / 45%, subsidence 5% / 8%; contents theft 41% / 47%,
accidental_damage 34% / 8%, escape_of_water 17% / 14%, flood 9% / 31%. Fire and bodily injury are thin
(70 and 450 claims) but carry the cost. Nine buildings fire claims exceed 100,000 (max 361,093); the largest motor
claim is 155,655 (F-CLM-LARGE).

Report lag (matched claims): median 8 days, p90 37, p99 241, max 653; bodily injury median 127 days, subsidence 71.
Latest loss 2024-12-29, latest report 2024-12-30, no report before loss, no 2025 losses (F-CLM-VALUATION).
December 2024 shows 268 reported losses against ~400 per month earlier in 2024 (last-month under-reporting).
repairer_id is null on 46% and third_party_id on 71% of claims (present only where a repairer / third party exists).

## 5. Customers, addresses, weather, expenses, reference policies

**Customers (135,856).** Referenced by training rows 36,768, by test rows 130,226 (31,138 both; 99,088 test only).
A customer holds one policy per line; combinations in training: motor only 14,855, buildings+contents 6,001,
contents only 4,522, all three 4,074, contents+motor 3,092, buildings only 2,523, buildings+motor 1,701.
gender F 50.0% / M 50.0% (emerging only). occupation: 81 raw spellings of 20 titles (F-OCC-TEXT; 20 after cleaning),
null 12%. marital_status single 40% / married 38% / divorced 7% / widowed 3% / null 12%. household_size 1–7
(median 2, null 12%). prior_claims_5y 0 on 77%, 1 on 20%; licence_points 0 on 80%, 3 / 6 / 9 on 12 / 6 / 2%.
years_at_address median 6 (null 12%). customer_since_year equals the policy inception year (F-STAMP-SINCE-YEAR);
campaign_code null 20% overall but 0% for the 2025 cohort (F-STAMP-CAMPAIGN-NULL). email_domain, previous_insurer
(40 codes), branch_id (25) and marketing_segment (12) are close to uniform.

**Addresses (136,914).** All referenced, none missing. region E03 29%, E06 19%, E02 18%, E05 16%, E01 13%, E04 4%;
urban_density suburban 45% / urban 25% / rural 20% / dense_urban 10%; flood_zone 1–5 = 69 / 15 / 8 / 4 / 2%, null
2.9% (not at random: F-NULL-FLOOD-ZONE); distance_to_river_km median 2.4 (null 12%); elevation 0–60 m (median 7.5);
soil clay 31%, four others 14% each, null 12%; year_built 1862–2021; property_type semi 30% / detached 25% /
terraced 25% / flat 20%; roof pitched 79% / flat 9% / null 12%; bedrooms 1–7 (mode 3); energy_rating A–G, null 12%;
basement 15%, trees_within_5m 12%, listed 3%, solar 10%.

**Weather (410,742).** Complete grid of every address × 2023, 2024, 2025. Market means: hail_days 14.2,
wind_exposure_index 5.1, freezing_days 22.5, dry_summer_index 0.67, wildfire_index 0.53, rainfall 1,336 mm,
mean temperature 15.1 °C. Values vary by year within an address (sd across years: hail 6 days, rainfall 89 mm, temp
1.1 °C) and 2025 differs from 2023–24 (hail 11.4 vs 14–17; freezing 28.9 vs 17–21; rain 1,251 vs 1,378 mm), so the
2025 values are year-specific (F-WEATHER-2025).

**Expenses.** fixed_expense_per_policy 85 CU (developed 45); variable_expense 15% (12%); commission_direct 0;
commission_comparison_site **null** (developed 10%; F-EXPENSE-MISSING); commission_broker 20% (15%); premium_tax 8%
(12%); cat_reinsurance 12% of property risk premium (6%); target_profit_margin 8% (5%).

**Reference policies.** 20 rows in a wide 50-column schema; cell-for-cell copies of 20 test rows (7 motor, 7
buildings, 6 contents; 18 broker new business); numeric columns typed float because of cross-line nulls
(F-REF-POLICIES).

## 6. Missingness

| Column(s) | Null share | Structure |
|---|---|---|
| customers: occupation, marital_status, household_size, years_at_address | 11.8–12.2% | independent draws (binomial co-occurrence), same in train/test cohorts |
| addresses: distance_to_river_km, soil_type, roof_type, energy_rating | 11.9–12.1% | independent; uniform across regions |
| addresses: flood_zone | 2.9% | **not at random**: null addresses are closer to rivers, lower, and claim twice as often |
| motor: vehicle_age, engine_size_cc, overnight_parking | 11.9–12.2% (test 12.0–12.2%) | independent; uniform across channel / new_business |
| buildings: days_unoccupied, smoke_alarms | 11.9–12.1% | independent |
| contents: security_level, high_value_items | 11.8–12.3% | independent |
| customers: campaign_code | 20.2% | deterministic in join year (cohort stamp) |
| claims: repairer_id, third_party_id | 46% / 71% | structural (no repairer / third party) |
| expenses: emerging | 1 of 8 | missing loading |

No other column has nulls. Treatment: no imputation; nulls carried as an explicit unknown level (F-NULL-RANDOM-12PCT).

## 7. Links between tables

policy → customer: 1:1 within a line (policy_id and customer_id are both unique per line; the same customer appears
across lines). policy → address: one address per row; a policy changes address only through a mid-term second row
(motor rows reference 23,799 addresses for 23,722 policies). Every customer_id and address_id referenced by any
policy or test row exists in customers / addresses, and every customer and address is referenced at least once.
weather covers every address for every year including 2025. claims → policy rows by (policy_id, loss_date ∈ period):
9,222 of 9,258 raw claims match exactly one row, none match two; the 36 non-matching claims are the pre-inception
claims. claims.line always agrees with the policy_id prefix (M/B/C). reference_policies.row_id ⊂ test row_ids.
sample_submission.row_id = union of the test row_ids.

## 8. Structural differences from the developed data

| Aspect | Developed (Part 1) | Emerging (Part 2) |
|---|---|---|
| History | 4 accident years (2021–2024), ≈600–980k policy rows per line, 163k claims | 2 years (2023–2024), 27–47k rows per line, 9.3k claims (1/18 of the developed volume; ≈1,000 property claims per line) |
| Test year | 2025, 15% new business | 2025, 76% new business (acquired broker book incepting January 2025) |
| Channel mix | direct 40 / comparison 35 / broker 25 | broker 70 / direct 25 / comparison 5 |
| Age | integer age (+ date_of_birth) | 5 bands; test book younger |
| Customer attributes | credit_band; no gender | gender; no credit band |
| Motor attributes | annual_mileage, telematics | absent |
| Region codes | R01–R12 | E01–E06 (no mapping) |
| Construction codes | 11 spellings of 5 codes | 4 clean codes |
| Occupation | 20 clean titles | 81 spellings of the same 20 titles |
| Sampling | all years complete | 2023 is a survivor sample (100% persistence into 2024) |
| Data defects shared | exposure day counts, ×1,000 sums insured, campaign-code cohort stamp, contacts leakage, 2025 weather present | the same four, plus a 360-day-basis exposure cluster |
| Data defects not shared | 604 content-duplicate claims, 414 unlinked claims (lags up to 741 days) | 0 duplicates, 36 unlinked claims |
| Claims level (raw at valuation) | motor freq 0.13–0.15, severity 3,500–4,200; buildings freq 0.044, severity 8,700–10,300; contents freq 0.040, severity 2,700–2,900 | motor freq 0.17–0.19, severity 2,200–2,300; buildings freq 0.045, severity 6,900–11,300; contents freq 0.034, severity 2,600 |
| Peril cost mix | buildings fire 23%, escape_of_water 23%, flood 28% | buildings fire 45%, flood 22%, escape_of_water 11% |
| Climate | 12.6 °C, 1,040 mm, hail 6 days, freezing 38 days | 15.1 °C, 1,336 mm, hail 14 days, freezing 22 days |
| Expense loadings | lower (fixed 45, broker 15%, tax 12%, cat 6%) | higher (fixed 85, broker 20%, tax 8%, cat 12%); comparison-site commission missing |
| Extra tables | — | expenses, reference_policies |

## 9. Reconciliation (phase 1 rungs of the ladder)

| Rung | Raw | Cleaned | Explained by |
|---|---|---|---|
| Rows, policies_motor / buildings / contents | 47,283 / 27,447 / 34,566 | same | no rows removed |
| Rows, test_motor / buildings / contents | 90,521 / 52,295 / 66,247 | same | no rows removed |
| Exposure, training (years) | 54,429.5 / 33,783.1 / 38,892.9 | 38,968.5 / 23,468.0 / 29,058.0 | 114 day-count rows (−15,461 / −10,315 / −9,835), 494 rows on 360-day basis (−0.4 each line), rounding |
| Exposure, test | 79,006.9 / 47,376.3 / 59,016.4 | 79,007.0 / 47,376.4 / 59,016.5 | rounding only |
| Claims count | 9,258 | 9,222 | 36 pre-inception claims excluded |
| Incurred to date | 28,995,103.17 | 28,898,003.92 | −97,099.25 on the 36 excluded claims |
| Net incurred, non-repudiated | 28,090,258.83 | 27,997,991.57 | −92,267.26 on the 36 excluded claims |
| Σ y in modelling tables vs cleaned claims net (repudiated = 0) | — | 27,997,991.57 = 27,997,991.57 | exact |
| Customers / addresses / weather / expenses / reference / sample rows | 135,856 / 136,914 / 410,742 / 8 / 20 / 209,063 | same | occupation values normalised (59,899 cells), nothing else touched |

One line per table: policies_* and test_*: exposure recomputed from dates, sum_insured ÷1,000 on the ratio-flagged
rows, nothing else; claims: 36 rows excluded; customers: occupation normalised; addresses, weather, expenses,
reference_policies, sample_submission: copied through.
