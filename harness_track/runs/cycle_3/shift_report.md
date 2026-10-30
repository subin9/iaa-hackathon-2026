# Shift report — emerging market (training 2023–2024, test 2025) vs developed market (2021–2024)

All emerging figures are on cleaned data (exposure recomputed from dates, ×1,000 sums insured
repaired, 36 unlinked claims excluded). Claims are valued at 31 December 2024 in both markets;
§4 is raw at that date unless marked "ultimate" (completion-adjusted, see target_notes.md).
Distribution distance = PSI with decile bins of the reference distribution (nulls as their own bin
in §2; separately reported in §3). Supporting tables: `work/psi_table.csv`,
`work/psi_dev_vs_emg_nonnull.csv`, `work/market_compare_line_year.csv`, `work/market_compare_peril.csv`,
`work/adversarial_single_auc.csv`.

## 1. Schema differences

Developed-only: integer `driver_age` / `policyholder_age`, `date_of_birth`, `credit_band`,
`annual_mileage`, `telematics_opt_in`, `telematics_score`. Emerging-only: `gender`, the five-band
age columns, the `expenses` and `reference_policies` tables. Same name but different encoding:
`construction_type` (11 free-text spellings ↔ 4 codes, mapped brick/wood/stone/non-standard),
`region` (R01–R12 ↔ E01–E06, **not mappable**), `occupation` (clean ↔ noisy, normalised),
`vehicle_age` (floor of 3 in the emerging market). Full mapping: `schema_mapping.md`.

## 2. Emerging train (2024) vs emerging test (2025)

Top shifts, all rows (PSI; interpretation):

| Column | PSI | Interpretation |
|---|---|---|
| exposure / row_days | 2.39 / 2.39 | (c) time identity of the row shape: 2025 rows are clipped at 31 Dec and 90% incept in January (mean exposure 0.87 vs 1.0+ in 2024 full-year rows). Exposure is the offset, never a feature. |
| customer_since_year | 2.03 | (c) join-year stamp (all acquired customers = 2025). Excluded. |
| renewal_count / new_business | 1.77 / 1.74 | (a) **portfolio mix**: new business 15% → 76%; renewal_count 0 for 76% of test rows. Kept as features (meaning unchanged). |
| campaign_code | 1.51 | (c) nullness = joined before 2023. Excluded. |
| weather: dry_summer_index, mean_temperature_c, freezing_days, hail_days, wildfire_index, rainfall_mm | 0.96 / 0.88 / 0.78 / 0.73 / 0.48 / 0.45 | (c) **calendar stamp**: 2025 is colder, drier, less hail for every address; identical PSI on renewal-only rows where nothing else changed. Excluded from the baseline. |
| years_licensed (motor) | 0.18 | (a) mix: younger drivers (median 23 → 13 years). |
| customer_service_contacts | 0.12 | (c) leakage (in-period count; tail only in training). Excluded. |
| marketing_segment | 0.06 | (a) mix: young_* segments 19% → 26%. |
| age band | 0.045 | (a) mix: 17-24 + 25-34 = 40% → 50% of rows (acquired book skews young and 65+). |
| written_premium, sum_insured, discount_applied | ≤ 0.04 | (a) small mix effects (10% discount share 0.7% → 3.8%, a new-business discount). |
| everything else (vehicle, property, address, customer attributes, channel, region) | < 0.02 | no shift: the acquired book is drawn from the same population on every risk attribute except age/tenure. |

Renewal rows only (the same policies one year apart): only weather (0.46–0.98), campaign_code /
customer_since_year (0.17, the 2024 joiners now carry codes), renewal_count (0.08) and vehicle_age
(0.08, +1 year) move. Confirms that the all-rows shifts are the acquired book plus the calendar.

New-business share, channel, tenure, age and region: channel of the 2025 new business is
broker 70% / direct 25% / comparison 5% — identical to the existing book, so `channel` does **not**
identify the acquired portfolio; `new_business` (and customer_since_year = 2025) does. Region mix is
unchanged (PSI < 0.001).

## 3. Developed (2021–24) vs emerging (2023–24) training years

PSI on non-null values (null rates reported separately; developed motor rows without a customer
match, 10% of them, were dropped from the reference):

| Column | PSI | Interpretation |
|---|---|---|
| region | 14.3 | definition: different code lists / geographies (not mappable) |
| construction_type (buildings) | 16.2 | definition: free-text spellings vs codes (mapped; shares agree once mapped) |
| gender | — | emerging-only column |
| wildfire_index / rainfall / temperature / freezing_days / hail_days / dry_summer_index | 6.5 / 3.0 / 2.7 / 2.3 / 1.8 / 1.4 | **different climate** (hotter, wetter, hail- and wildfire-prone, fewer frosts) — a risk-behaviour difference that shows up in the peril mix (§4), not something to model through weather values |
| channel | 1.13 | mix: broker 25% → 70%, comparison site 35% → 5% |
| vehicle_age (motor) | 0.89 | definition/mix: no vehicles under 3 years; median 7 → 10 |
| customer_since_year | 0.73 | different history windows; irrelevant after tenure transform |
| wind_exposure_index | 0.18 | climate (slightly windier) |
| discount_applied | 0.17 | mix: 2.5% → 1.3% mean discount |
| fuel_type | 0.09 | mix: electric 8% → 2% |
| tenure (contents) | 0.07 | mix: renters 30% → 43% |
| marketing_segment / age bands | 0.05 / 0.03 | mix: younger (17-24 14% → 21%, 65+ 31% → 28%) |
| all other shared attributes | < 0.03 | same distributions (same generator of risk attributes) |

Null rates differ (2.5% developed vs 12% emerging on the same attribute columns) — a data-capture
difference, treated as an "unknown" level in both.

## 4. Frequency, severity and peril mix by line (raw, valued 31 Dec 2024; per exposure-year)

| Line | Market | Year | Exposure-yrs | Freq | Mean claim | Burning cost | BC capped 25k | BC capped 50k | BC capped 100k |
|---|---|---|---|---|---|---|---|---|---|
| motor | developed | 2021 | 187,992 | 0.146 | 3,870 | 564 | 476 | 522 | 545 |
| motor | developed | 2022 | 199,699 | 0.149 | 3,932 | 585 | 493 | 540 | 566 |
| motor | developed | 2023 | 199,682 | 0.140 | 4,191 | 588 | 468 | 497 | 515 |
| motor | developed | 2024 | 199,786 | 0.129 | 3,506 | 454 | 416 | 435 | 445 |
| motor | emerging | 2023 | 18,865 | 0.189 | 2,295 | 433 | 406 | 419 | 430 |
| motor | emerging | 2024 | 20,104 | 0.174 | 2,204 | 383 | 363 | 375 | 380 |
| buildings | developed | 2021 | 140,783 | 0.044 | 8,716 | 384 | 259 | 317 | 356 |
| buildings | developed | 2022 | 149,872 | 0.045 | 9,059 | 411 | 278 | 337 | 379 |
| buildings | developed | 2023 | 149,987 | 0.046 | 9,519 | 433 | 292 | 357 | 402 |
| buildings | developed | 2024 | 149,918 | 0.044 | 10,250 | 449 | 296 | 363 | 411 |
| buildings | emerging | 2023 | 11,373 | 0.046 | 11,269 | 514 | 267 | 348 | 408 |
| buildings | emerging | 2024 | 12,095 | 0.044 | 6,909 | 307 | 205 | 242 | 273 |
| contents | developed | 2021 | 140,931 | 0.040 | 2,665 | 106 | 103 | 105 | 106 |
| contents | developed | 2022 | 149,986 | 0.040 | 2,662 | 107 | 105 | 107 | 107 |
| contents | developed | 2023 | 149,975 | 0.041 | 2,848 | 117 | 113 | 116 | 117 |
| contents | developed | 2024 | 149,967 | 0.040 | 2,925 | 117 | 113 | 116 | 117 |
| contents | emerging | 2023 | 14,108 | 0.035 | 2,618 | 91 | 90 | 91 | 91 |
| contents | emerging | 2024 | 14,950 | 0.034 | 2,560 | 87 | 83 | 87 | 87 |

Like-for-like (R-0411, fixed caps) reading per line:

- **Motor**: frequency 35% higher than developed (0.189 vs 0.140 in 2023), severity 55% of developed
  (2,295 vs 4,191). Capped at 25k the burning cost is 87% of developed; raw 74%. Every peril's mean
  cost is lower (own damage 1,085 vs 1,841; third-party property 2,429 vs 3,608; theft 3,759 vs 5,969;
  bodily injury 10,491 vs 21,582) — a cost/compensation-level difference, not mix. Peril mix by cost
  share (2023 vs developed 2021–23): bodily injury 34% vs 42%, third-party property 33% vs 27%,
  own damage 18% vs 20%, theft 9% vs 8%, glass/hail 5% vs 4%; glass/hail **frequency** is 46%
  higher (0.032 vs 0.022 per year — consistent with 14 vs 6 hail days).
- **Buildings**: frequency identical (0.046 vs 0.046). Capped at 50k the 2023 burning cost is the same
  as developed (348 vs 357); raw it is 19% higher because **fire** is 55% of 2023 cost against 23% in
  the developed market: fire frequency 0.0043 vs 0.0018 per year (2.4×; wildfire index 0.53 vs 0.16),
  similar fire severity (66k vs 52k). Escape of water is half the developed burning cost (44 vs 94;
  frequency 0.0115 vs 0.0172, severity 3.9k vs 5.7k — 19 vs 38 freezing days). Storm, flood,
  subsidence are at developed levels. 2024 looks 40% lighter than 2023 because 2023 had 49 fire
  claims and 2024 has 21 (the single largest driver of the two-year level uncertainty, F-11).
- **Contents**: frequency 15% lower (0.035 vs 0.041), severity 8% lower; burning cost 78% of
  developed. Flood is a larger share (34% vs 25%), escape of water smaller (15% vs 23%), theft the
  same (43% vs 41%).

Thin perils (say so): emerging fire 70 claims, subsidence 52, buildings flood 81, contents flood 86,
bodily injury 450 (open-heavy). Peril-level severities for these carry ±25–40% sampling error.

Open claims at the valuation date: 2024 open share by count 20% motor / 25% buildings / 12% contents
(developed 21% / 25% / 13%) — the two markets are at the same development stage, which makes the
developed curve a usable tail (target_notes.md §3).

## 5. Acquired-portfolio check (within emerging training data)

76% of 2025 test rows are new business from the broker transfer; their policies are absent from
training, and `channel` does not single them out. The nearest training analogue is the
new-business segment of 2023–24 (motor 6,535 rows / 697 claims; buildings 3,786 / 77; contents
4,716 / 102), which has the **same age mix** as the 2025 book (17-24 28%, 25-34 26%, 35-49 11%,
50-64 12%, 65+ 23%) and the same channel split.

Frequency and burning cost per exposure-year, new business vs renewals (2023–24, repaired exposure):

| Line | Segment | Exposure-yrs | Freq | Burning cost | Age-standardised ratio NB/renewal (freq, cost) |
|---|---|---|---|---|---|
| motor | new business | 3,040 | 0.229 | 620 | **1.18, 1.43** |
| motor | renewal | 35,929 | 0.177 | 389 | |
| buildings | new business | 1,810 | 0.043 | 338 | 0.93, 0.82 (thin: 77 claims) |
| buildings | renewal | 21,658 | 0.045 | 414 | |
| contents | new business | 2,234 | 0.046 | 113 | **1.29, 1.23** (102 claims) |
| contents | renewal | 26,825 | 0.033 | 86 | |

Declared history is similar (prior_claims_5y: 77% zero in both segments; motor ncb_years 5.5 vs 6.5,
years_licensed 21 vs 28 — the age effect). Persistence of first-year policies: all 2023 new business
is present in 2024 (survivor year); of those, 17.7% lapsed or cancelled during 2024 against 14.9% for
older policies. Rows after a mid-term change run at higher frequency in motor (0.20 vs 0.17).

Can the 2025 book be assumed to behave like the renewal book? **No.** Motor new business carries a
clear excess beyond age (≈+18% frequency, +40% cost); contents likewise; buildings is too thin to
say. The training segment is large enough to estimate a new-business relativity for motor, marginal
for contents, not for buildings; the model will be extrapolating a 15% segment to 76% of the book,
with the age mix (young and 65+) inside the training support.

## 6. Leakage checks

Adversarial validation, 2024 training rows vs 2025 test rows (LightGBM, 3-fold out-of-fold AUC):

| Feature set | motor | buildings | contents |
|---|---|---|---|
| all candidates | 1.000 | 1.000 | 1.000 |
| excluding stamps and row shape (customer_since_year, campaign_code, customer_service_contacts, exposure, row_days, start_month) | 0.997 | 0.997 | 0.998 |
| also excluding new_business / renewal_count / discount (mix) | 0.996 | 0.996 | 0.996 |
| also excluding weather | **0.819** | **0.856** | **0.879** |
| renewal rows only, last set | 0.720 | 0.745 | 0.743 |

Single-feature AUC ≥ 0.6: customer_since_year 0.88, exposure/row_days 0.83–0.84, renewal_count 0.82,
new_business 0.80, campaign_code 0.79, the six weather indices 0.68–0.77, years_licensed 0.61 (motor).
Everything else ≤ 0.56. The 0.82–0.88 residual is portfolio mix (new business, young ages,
year_built/building-age interactions that fingerprint the acquired addresses) and should be
explained, not removed (R-0019). The 0.72–0.75 on renewal rows comes from attributes that advance by
exactly one year for the same policy (vehicle_age, years_licensed, building_age) and is not leakage.

Columns whose distribution exists only in training: `customer_service_contacts` tail (>6, 1.5% of
training rows, absent in test), `renewal_decision` (end-of-period). Both excluded. `missed_payments_12m`
and `days_quote_to_inception` have the same range and shape in test and were kept.

## 7. Implications for modelling

- **Drop** as features: customer_since_year, campaign_code, customer_service_contacts, renewal_decision,
  the seven weather indices (2025 is a different weather year for every address), row shape
  (start month, row length) and written_premium; exposure stays in the offset.
- **Keep as mix**: new_business, renewal_count, age band, years_licensed, discount_applied — and
  evaluate on the new-business subset; compare the fitted new-business relativity with the pre-model
  +18% / +40% (motor) and +29% / +23% (contents) figures.
- **Re-estimate levels** on emerging data: motor is high-frequency/low-severity, property is fire-
  and flood-heavy; developed base rates do not transfer (motor burning cost 74% of developed,
  buildings ≈ 100% capped / 119% raw, contents 78%).
- **Borrow shape, not level**: developed relativities for shared attributes (age bands after
  banding, vehicle, property, construction mapped) are a usable prior; region, weather, mileage,
  telematics, credit band are not available or not mappable.
- **Borrow the tail and the trend**: completion beyond 540 days (2.3% of motor cost) and the
  annual trend (motor ≈ 0%, buildings +6%, contents +5% from developed 2021–23) cannot be
  estimated here; both are listed with sensitivities in adaptation_decisions.md.
- **Watch**: buildings level (2023 fire year vs 2024: ±30% between the two years); open bodily-injury
  reserves (38% of 2024 motor cost sits in open claims); the survivor-year composition of 2023 in
  the single time fold; `declined_by_insurer` semantics; the null comparison-site commission in the
  premium build.
