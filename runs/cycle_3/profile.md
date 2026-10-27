# Profile of the emerging-market data

Scope: `./data/emerging/` as delivered (read-only), profiled before any cleaning. Comparisons with
`./data/developed/` are structural only; no join between the two markets was made. Claims in both
markets are valued at 31 December 2024. Amounts in CU.

Environment: Python 3.12.9, polars 1.42.1, pyarrow 24.0.0, pandas 3.0.1, numpy 2.4.3,
scikit-learn 1.8.0, lightgbm 4.7.0, scipy 1.17.1, jsonschema 4.26.0. Threads capped at 6; seeds fixed.
Scripts in `./work/` (p01–p16 profiling, p20 cleaning, p21 findings, p30–p32 targets, p40 baseline).

## 1. Tables, sizes and keys

| Table | Rows | Key | Notes |
|---|---|---|---|
| policies_motor | 47,283 | row_id (unique) | 23,722 policies; 2023: 21,680 rows, 2024: 25,603 |
| policies_buildings | 27,447 | row_id | 14,299 policies; 2023: 12,580, 2024: 14,867 |
| policies_contents | 34,566 | row_id | 17,689 policies; 2023: 15,834, 2024: 18,732 |
| test_motor | 90,521 | row_id | 83,907 policies, all 2025 |
| test_buildings | 52,295 | row_id | 50,300 policies, all 2025 |
| test_contents | 66,247 | row_id | 62,636 policies, all 2025 |
| sample_submission | 209,063 | row_id | = test rows (M 90,521 + B 52,295 + C 66,247); prediction 0.0 |
| claims | 9,258 | claim_id (unique) | motor 7,183, buildings 1,059, contents 1,016 |
| customers | 135,856 | customer_id (unique) | every id referenced by a policy or test row; 99,088 appear only in test |
| addresses | 136,914 | address_id (unique) | every id referenced |
| weather | 410,742 | (address_id, year) | 136,914 addresses × years 2023, 2024, 2025 (test year included) |
| expenses | 8 | item | developed and emerging columns; one null (comparison-site commission) |
| reference_policies | 20 | row_id | 7 motor / 7 buildings / 6 contents, all 2025 test rows, wide schema of all three lines |

Identifiers: row_id = line prefix (M/B/C) + 8 digits, contiguous ranges per table (training
M00000000–M00075696, test M00109296–M00199816, etc.); policy_id = prefix + 8 digits; customer_id 8 digits;
address_id A + 7 digits; claim_id CL + 8 digits. Policy prefix always agrees with claims.line.

Links (all 100%): policy→customer, policy→address, (address, year)→weather, for train and test.
Claims→policy by policy_id: 100%; claims→policy **row** by loss date inside the row period: 9,222 of
9,258 (99.6%), none ambiguous (see §6). A policy keeps one customer across rows; 7,203 policies change
address between rows (buildings: every mid-term change is a home move; motor: moves only at renewal).

## 2. Row structure and time

A "policy row" is a **365-day policy year or a segment of it**, never spanning a calendar year:
80% of training rows start on 1 January; new business incepts through the year and runs to
31 December; a `mid_term_change` closes a row and the next row starts the following day (up to 4
rows per policy over the two years). Full-year 2024 rows run 1 Jan–30 Dec (365 days in a leap
year) so 31 Dec 2024 is uncovered by any row; no claim falls on that date.

Test rows (2025): 90% start in January (22% on 1 Jan), all clipped at 2025-12-31; 76% are new
business whose policy_id never appears in training (the acquired broker book); the other 24% are
2024 policies whose last decision was `renewed` (or `declined_by_insurer`, see §8). None of the
8,574 policies that lapsed or cancelled in 2024 is in the test set.

Exposure convention: `exposure = (period_end − period_start + 1) / 365`, 4 dp (a 365-day row = 1.0;
a 1-day row = 0.0027). 99.5% of rows follow it; two anomaly clusters are described in §7.

Persistence (R-0020): **100% of 2023 policies appear in 2024 in every line; 2023 contains no
`lapsed_by_customer` or `cancelled` decision** (only renewed / mid_term_change / declined), whereas
2024 shows 15.3% lapse+cancellation. 2023 is a survivor sample. The developed data has the same
structure in its first year (2021: 100% persistence, no lapses; 2022–24: 85%).

## 3. Policy attributes (training, as delivered)

Motor (36 columns): driver_age_band (5 bands; 65+ 28%, 17-24 20%, 25-34 19%, 50-64 17%, 35-49 16%),
years_licensed 0–73 (consistent with band: 17-24 max 7), ncb_years 0–15, vehicle_value_group 1–20,
vehicle_age **3–26** (no vehicle younger than 3; developed 0–28), make_model 300 codes (all also in
developed), engine_size_cc 500–3,600 in 100 cc steps, body_type 5, transmission 2, seats 2–7,
vehicle_colour 8 (uniform), fuel_type (petrol 54%, diesel 30%, hybrid 15%, electric 2%),
cover_type (comprehensive 79%), overnight_parking (driveway/street/garage, 12% null), vehicle_use,
named_young_driver 5%, voluntary_excess {0,250,500,1000}, compulsory_excess constant 250,
channel (broker 70%, direct 25%, comparison_site 5%), payment_method, missed_payments_12m 0–5,
new_business 14%, renewal_count 0–16, days_quote_to_inception 0–30, discount_applied {0,.05,.10},
written_premium 193–2,199 (annual premium, not pro-rated for short rows), customer_service_contacts 0–20,
renewal_decision (renewed 85%, mid_term_change 7%, lapsed 5%, cancelled 3%, declined 0.5%).

Buildings (27): policyholder_age_band, sum_insured 44k–813k plus a ×1,000 cluster (§7),
construction_type codes BRK 70% / WOD 12% / MIX 10% / STN 8%, occupancy (owner_occupied 90%),
days_unoccupied 0–14 (95%) or 31–119 (5%; same bimodal shape in the developed data), smoke_alarms 85%
(12% null), accidental_damage_cover 40%, mortgage 55%, compulsory_excess 350, premium 63–4,630.

Contents (28): sum_insured 5.2k–235k plus ×1,000 cluster, tenure (owner 57% / renter 43%),
security_level 3 levels (12% null), high_value_items 0–5 (12% null), works_from_home 25%,
lodgers 5%, bicycle_cover 15%, premium 27–573.

Customers (17): gender (50/50; developed has date_of_birth instead and a credit_band the emerging
market lacks), occupation (81 raw spellings of a 20-value list, §7), marital_status, household_size 1–7,
prior_claims_5y 0–5 (mean 0.27), licence_points 0–9, years_at_address 0–53, customer_since_year
2008–2025 (99,088 customers = 2025; equals policy year − renewal_count exactly), email_domain 5,
marketing_consent, document_preference, previous_insurer 40 codes (uniform), campaign_code 15 codes
or null, branch_id 1–25, marketing_segment 12 (age part is a function of the age band).

Addresses (16): region E01–E06 (6 codes; developed R01–R12), urban_density 4, flood_zone 1–5 (3% null),
distance_to_river_km, elevation_m 0–60 (developed to 197), soil_type 5, year_built 1862–2021,
property_type 4, roof_type, basement 15%, trees_within_5m 12%, listed_building 3%, bedrooms 1–7,
energy_rating A–G, solar_panels 10%. Apart from region codes and elevation the distributions match
the developed market closely.

Weather (7 indices per address-year): a different climate from the developed market — hail days
14 vs 6, rainfall 1,336 vs 1,045 mm, mean temperature 15.1 vs 12.7 °C, wildfire index 0.53 vs 0.16,
freezing days 22 vs 38. Year-to-year correlation per address 0.92–0.95; 2025 is systematically
colder/drier (freezing days 29, rainfall 1,251, hail 11).

## 4. Missingness

About 12% in each of: motor vehicle_age / engine_size_cc / overnight_parking; buildings
days_unoccupied / smoke_alarms; contents security_level / high_value_items; customers occupation /
marital_status / household_size / years_at_address; addresses distance_to_river_km / soil_type /
roof_type / energy_rating (flood_zone 3%). Rates are identical in 2023, 2024, test, new business and
renewals; nulls are independent across columns (joint null rate = product of marginal rates); claim
frequency of null vs non-null rows differs by less than noise on repaired exposure. Treated as
missing-completely-at-random (kept as an "unknown" level, no imputation, no indicators). The developed
market has 2.5% in the same columns. campaign_code null (20%) is **not** random: it marks customers
who joined before 2023 (§8).

## 5. Claims

9,258 claims; status closed 8,082 / open 1,056 / repudiated 120 (all amounts 0). Loss dates
2021-10-27 to 2024-12-29, report dates 2023-01-02 to 2024-12-30 (consistent with valuation
2024-12-31; nothing in the test period). Perils: motor own_damage 2,712, third_party_prop 2,263,
glass_hail 1,350, bodily_injury 450, theft 408; buildings storm 466, escape_of_water 268,
accidental_damage 122, flood 81, fire 70, subsidence 52; contents theft 418, accidental_damage 340,
escape_of_water 172, flood 86. third_party_id present for exactly the two third-party perils,
repairer_id for own_damage and third_party_prop.

Amounts: paid ≤ incurred always, closed ⇒ paid = incurred, recoveries ≤ incurred (8% of claims have
recoveries, mostly motor own damage). Net incurred (incurred − recoveries) 28.09M in total:
motor 15.92M, buildings 9.58M, contents 2.59M. Nine buildings fire claims exceed 160k (max 361k);
the largest motor claim is a 156k open bodily-injury claim. No power-of-ten cluster in any amount.

Report lag: median 8 days, 90% 37, 99% 241 (all perils ≤ 90 days at the 99th percentile except
bodily injury 586 and subsidence 254). December 2024 has 263 claims against a 388 monthly mean.
Open share 2023: 3.7% motor / 4% buildings / 0% contents; 2024: 20% / 25% / 12% — the same profile
as the developed market's latest year.

Frequency and burning cost on **repaired** exposure (raw, at the valuation date, before completion):

| Line | Year | Exposure-years | Claims | Frequency | Net incurred | Burning cost / yr | Mean claim |
|---|---|---|---|---|---|---|---|
| motor | 2023 | 18,865 | 3,557 | 0.189 | 8.16M | 433 | 2,295 |
| motor | 2024 | 20,104 | 3,491 | 0.174 | 7.69M | 383 | 2,204 |
| buildings | 2023 | 11,373 | 519 | 0.046 | 5.85M | 514 | 11,269 |
| buildings | 2024 | 12,095 | 537 | 0.044 | 3.71M | 307 | 6,909 |
| contents | 2023 | 14,108 | 491 | 0.035 | 1.29M | 91 | 2,618 |
| contents | 2024 | 14,950 | 507 | 0.034 | 1.30M | 87 | 2,560 |

(Before the exposure repair the denominators were 25,536 / 28,893 motor, 16,891 / 16,892 buildings,
19,021 / 19,872 contents; stored exposure overstated the book by 28–44%.)

## 6. Linkage of claims to policy rows

A claim belongs to the row of its policy whose period contains the loss date. 9,222 claims link to
exactly one row; 36 do not: every one has a loss date **before its policy's first row** (34 before the
market's first row on 2023-01-01) with report lags of 411–565 days, beyond the 99th percentile of the
matched distribution for their perils. They are excluded as date defects (findings F-08, team query).
No claim belongs to a policy that is absent from the policy tables or present only in test.

## 7. Data-quality issues found (summary; full detail and ids in findings.json)

| Id | Issue | Rows | Action |
|---|---|---|---|
| F-01 | exposure stored as a day count (×365), training only | 114 | recompute from dates |
| F-02 | exposure on a 360-day basis (×1.0139), training only | 495 | recompute from dates |
| F-03 | test files: exposure clean (negative result) | 0 | none |
| F-04/05 | sum_insured ×1,000 (buildings 53 train + 104 test; contents 57 + 135), identified by log10(SI/premium) > 4 inside an empty interval | 349 | ÷1,000 |
| F-06/07 | no unit cluster in claim amounts / premiums; no duplicate claims (negative results) | 0 | none |
| F-08 | claims with loss date before the policy's first row, implausible lags | 36 | exclude, query |
| F-15 | occupation case / whitespace / uniform "Self-employed" prefix noise | 59,899 values | normalise to the 20-value list |
| F-09–F-25 | valuation-date and last-month reporting, survivor year, dominant large losses, leakage column, join-year stamps, MCAR nulls, null comparison-site commission, `declined_by_insurer` persisting, 30-Dec row ends, repudiated claims, new-business dominance, 2025 weather, reference table, vehicle_age floor, one-day rows | — | flag only |

Reconciliation after cleaning (R-0012/R-0017): every policy, customer, address and weather table
keeps its row count; claims 9,258 → 9,222 (−36, F-08); net incurred 28,090,259 → 27,997,992
(−92,267, F-08); exposure motor 54,429 → 38,969, buildings 33,783 → 23,468, contents 38,893 → 29,058
(F-01/F-02); sum insured totals fall by the ×1,000 rows only (F-04/F-05); sum of `y` in the modelling
tables = 27,997,991.57 = cleaned non-repudiated net incurred. Unexplained movement: none.

## 8. Leakage and time identity (detail in shift_report.md)

- `customer_service_contacts` grows mechanically with claims (0 contacts → 0.01% claim rate; 4+ → 94%)
  and its tail exists only in training → excluded from features.
- `campaign_code` is null exactly for pre-2023 joiners; `customer_since_year` is the join year
  (= policy year − renewal_count) → both excluded; `renewal_count` / `new_business` kept as tenure/mix.
- Weather values for 2025 differ systematically from 2023–24 for every address → a calendar stamp here;
  excluded from the baseline feature set.
- `renewal_decision` is end-of-period information (excluded). Its `declined_by_insurer` value does not
  terminate a policy (all declined 2023 policies are in 2024; 167 of 181 declined 2024 policies are in
  the 2025 test) — flagged for a human (F-18).
- Adversarial validation 2024-train vs 2025-test: AUC 1.00 with everything, 0.82–0.88 after removing
  stamps, weather and row shape; the remainder is the acquired book's mix (new business, young ages).

## 9. Structural differences from the developed data

| Aspect | Developed (Part 1) | Emerging (Part 2) |
|---|---|---|
| Training years | 2021–2024 (4), first year a survivor year | 2023–2024 (2), first year a survivor year |
| Training rows / claims | ≈2.4M rows, 163k claims | 109k rows, 9.3k claims |
| Test | 2025, 627k rows, 15% new business | 2025, 209k rows, 76% new business (acquired book) |
| Age | integer driver_age / policyholder_age | 5 age bands only |
| Customer | date_of_birth, credit_band | gender; no DOB, no credit band |
| Motor | annual_mileage, telematics_opt_in, telematics_score | not recorded |
| construction_type | 11 free-text spellings (Brick/brick/BRICK, W/w, T/t, stone/STONE, non_standard) | 4 codes BRK/WOD/STN/MIX |
| region | R01–R12 | E01–E06 (different geography) |
| occupation | clean 20 values | 81 noisy spellings |
| Nulls in attribute columns | 2.5% | 12% |
| Channel mix | direct 40 / comparison 35 / broker 25 | broker 70 / direct 25 / comparison 5 |
| Extra tables | — | expenses (both markets), reference_policies (20 quotes) |
| Weather years | 2021–2025 | 2023–2025 |
| Shared defects | day-count & 360-day exposures, ×1,000 sums insured, campaign_code stamp, survivor first year | same |
