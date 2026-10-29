# Shift report — emerging market

Computed on the cleaned emerging tables (`outputs/cleaned/`) and the as-delivered developed tables with exposure recomputed from dates in both markets. Claims at the 31 Dec 2024 valuation, raw (no IBNR adjustment) unless stated. Script: `work/p12_shift.py`; statistics in `work/shift_stats.json`.

## 1. Schema differences

See `schema_mapping.md`. In one line each: developed-only `date_of_birth`, `credit_band`, `driver_age`/`policyholder_age` (integer), `annual_mileage`, `telematics_opt_in/score`; emerging-only `gender`, `driver_age_band`/`policyholder_age_band` (5 bands); re-encoded `construction_type` (free text → 4 codes), `region` (R01–R12 vs E01–E06, unmappable), `occupation` (clean list vs noisy free text). Ages are mapped to the emerging bands, construction to the emerging codes, region kept market-specific, credit/mileage/telematics dropped.

## 2. Emerging train (2024) vs emerging test (2025)

PSI on non-null values of every shared column; null-rate differences reported separately (R-0402). Nulls are 12% in both years for the same 14 columns, so no shift is a null artefact. PSI ≥ 0.25 is a large shift, 0.1–0.25 moderate.

| Column | PSI motor | PSI buildings | PSI contents | Interpretation |
|---|---:|---:|---:|---|
| customer_since_year | 2.03 | 2.02 | 2.04 | **(c) time stamp** — 2025 joiners exist only in test. Excluded (F-11). |
| renewal_count / tenure_years | 1.77 | 1.76 | 1.77 | **(a) mix** — 76% of test rows are new business (renewal_count 0, tenure 0) vs 15% in 2024. Meaning unchanged (R-0019); kept, model evaluated on the new-business subset. |
| new_business | 1.74 | 1.73 | 1.75 | (a) mix — the acquired book. Kept. |
| years_licensed (motor) | 0.18 | — | — | (a) mix — younger drivers: median 13 years in test vs 24 in training. |
| customer_service_contacts | 0.12 | 0.06 | 0.04 | (c) leakage — training tail is claims-driven (F-13). Excluded. |
| marketing_segment | 0.06 | 0.07 | 0.06 | (a) mix — "young_*" segments 35% → 48%. |
| discount_applied | 0.05 | 0.05 | 0.05 | (a)/(b) — 10% discounts 0.7% → 2%; a pricing-practice difference of the broker book. Kept, weak. |
| age band | 0.05 | 0.05 | 0.04 | (a) mix — 17–34 share 40% → 50%, 65+ 28% → 24%, 35–64 32% → 26%. |
| ncb_years, written_premium | 0.04 | 0.02 | 0.01 | (a) mix following age. |
| campaign_code (null rate 75% → 17%) | 0.00 (values) | | | (c) stamp through the null bin (F-12). Excluded. |
| everything else | < 0.02 | < 0.01 | < 0.01 | no shift: channel (broker 70% / direct 25% / comparison 5% in both), region, payment method, vehicle, property and address attributes, missed_payments, prior_claims_5y. |

Adversarial validation (R-0006): AUC 1.00 with all columns, 0.82 without the two stamps (renewal_count/new_business = mix), **0.63 motor / 0.56 buildings / 0.56 contents** after also removing the new-business indicators. The residual separability is age/experience mix and high-cardinality mix (make_model, occupation, previous_insurer); no remaining single column has AUC > 0.56.

Notable non-shifts: channel mix is identical in 2024 and 2025, so **no channel flag singles out the acquired book**; its only marker is `new_business`/`renewal_count = 0` (and `customer_since_year = 2025`, a stamp). Region mix, property mix and declared history (`prior_claims_5y` mean 0.27 in every cohort) are unchanged.

## 3. Developed vs emerging (training years)

Same PSI on shared columns, developed 2021–2024 vs emerging 2023–2024.

| Column | PSI (motor / bldg / cont) | Interpretation |
|---|---|---|
| channel | 1.13 / 1.11 / 1.12 | **mix / distribution model**: developed direct 40%, comparison 35%, broker 25%; emerging broker 70%, direct 25%, comparison 5%. Different acquisition cost structure (see expenses table), not different risk per se. |
| vehicle_age | 1.05 / — / — | **possible definition change**: emerging has no vehicle under 3 years and is shifted ≈ +2 years throughout (quantiles 5/7/9/13/19 vs 2/5/7/10/16). Either an older fleet (plausible for the market) or age measured from a different date. Team query; treat as mix, do not borrow relativities below age 3. |
| customer_since_year | 0.93 / 0.88 / 0.90 | stamp in both markets (different join-year ranges). Excluded. |
| discount_applied | 0.22 / 0.22 / 0.22 | pricing practice: developed discounts 45% of rows, emerging 26%. |
| fuel_type | 0.09 / — / — | mix: electric 8% → 2%. |
| tenure (contents) | — / — / 0.07 | mix: renters 30% → 43%. |
| marketing_segment | 0.05 / 0.05 / 0.06 | mix: young segments 28% → 47%. |
| ncb_years, years_licensed, age band | 0.03–0.05 | mix: slightly younger, less experienced drivers (median years licensed 24 vs 28). |
| written_premium | 0.04 / 0.07 / 0.02 | level: medians 502 vs 480 (motor), 238 vs 217 (buildings), 119 vs 127 (contents). |
| sum_insured, elevation_m, soil_type | ≤ 0.02 | near-identical property mix; emerging elevations are capped lower (max 60 m vs 197 m); clay 35% vs 42%. |
| all other shared columns | < 0.01 | same distributions (voluntary excess, payment method, cover type, body type, property type, urban density, flood zone, bedrooms, year built, prior claims, licence points…). |

Null rates: developed 2.5% vs emerging 12% on the same 14 columns — a data-capture difference, not a shift in the underlying variable (null bins excluded from the PSI).

Weather (climate, not a shift in a feature): emerging is warmer (15.5 vs 12.7 °C), wetter (1,378 vs 1,046 mm), with 2.3× the hail days, half the freezing days and 3.5× the wildfire index. Weather is not a feature (R-0022, R-0302), but the climate difference is the prior reason to expect a different peril mix (glass/hail up, freeze-related escape of water down).

## 4. Frequency, severity and peril mix by line (per exposure-year, raw at 31 Dec 2024)

Developed accident years 2021–2024, emerging 2023–2024. Severity and burning cost shown uncapped | capped at 25k per claim | capped at 100k (R-0411). Developed 2024 and emerging 2024 are incomplete (12 months' development); emerging 2023 is 97–100% complete, developed 2021–2023 are mature.

**Motor**

| Market, AY | Exposure | Claims | Frequency | Severity (uncapped / 25k / 100k) | Burning cost (uncapped / 25k / 100k) |
|---|---:|---:|---:|---|---|
| developed 2021 | 187,992 | 27,356 | 0.146 | 3,871 / 3,266 / 3,744 | 563 / 475 / 545 |
| developed 2022 | 199,699 | 29,691 | 0.149 | 3,931 / 3,313 / 3,799 | 585 / 493 / 565 |
| developed 2023 | 199,682 | 27,990 | 0.140 | 4,191 / 3,333 / 3,667 | 588 / 467 / 514 |
| developed 2024 (immature) | 199,786 | 25,864 | 0.129 | 3,506 / 3,214 / 3,440 | 454 / 416 / 445 |
| emerging 2023 | 18,865 | 3,557 | **0.189** | **2,295** / 2,153 / 2,279 | 433 / 406 / 430 |
| emerging 2024 (immature) | 20,104 | 3,491 | 0.174 | 2,204 / 2,092 / 2,188 | 383 / 363 / 380 |

Emerging motor has **30% higher frequency and 45% lower severity** than the developed market; burning cost is 25% lower. Peril mix by cost (emerging 2023 vs developed 2023): bodily injury 34% vs 41%, third-party property 33% vs 27%, own damage 18% vs 19%, theft 9% vs 9%, glass/hail 5% vs 4% (8% in emerging 2024). By count, glass/hail is 19% of emerging claims vs 14% developed. Reading: more, smaller claims — a lower-cost repair/compensation environment with more hail; the long-tail bodily-injury share is somewhat lower. 7,048 non-repudiated claims: frequency and mix are credible; severity by peril for bodily injury (450 claims) and theft (408) is moderately credible.

**Buildings**

| Market, AY | Exposure | Claims | Frequency | Severity (uncapped / 25k / 100k) | Burning cost (uncapped / 25k / 100k) |
|---|---:|---:|---:|---|---|
| developed 2021 | 140,783 | 6,195 | 0.044 | 8,725 / 5,886 / 8,077 | 384 / 259 / 355 |
| developed 2022 | 149,872 | 6,792 | 0.045 | 9,059 / 6,130 / 8,355 | 411 / 278 / 379 |
| developed 2023 | 149,987 | 6,817 | 0.046 | 9,510 / 6,409 / 8,828 | 432 / 291 / 401 |
| developed 2024 (immature) | 149,918 | 6,571 | 0.044 | 10,250 / 6,744 / 9,382 | 449 / 296 / 411 |
| emerging 2023 | 11,373 | 519 | 0.046 | 11,269 / 5,850 / 8,933 | 514 / 267 / 408 |
| emerging 2024 (immature) | 12,095 | 537 | 0.044 | 6,909 / 4,620 / 6,142 | 307 / 205 / 273 |

Frequency is the same as the developed market. Severity and level depend entirely on the cap: uncapped, emerging 2023 is 20% above developed 2023 and emerging 2024 30% below; at a 25k cap both emerging years are 8–30% below developed. **Fire is 55% of 2023 emerging cost (10 claims over 125k) and 30% of 2024, against 22–24% in developed**; flood 18% / 29% vs 28%; escape of water 9% / 14% vs 23%; storm 9% / 19% vs 10–12%. With 1,056 claims and 70 fires, the buildings level is **thin**: the three cut-offs tell three stories about the same line (R-0411), and the fire share is the single largest uncertainty in the whole exercise.

**Contents**

| Market, AY | Exposure | Claims | Frequency | Severity (uncapped / 25k / 100k) | Burning cost (uncapped / 25k / 100k) |
|---|---:|---:|---:|---|---|
| developed 2021 | 140,931 | 5,583 | 0.040 | 2,663 / 2,589 / 2,663 | 106 / 103 / 106 |
| developed 2022 | 149,986 | 6,024 | 0.040 | 2,663 / 2,620 / 2,663 | 107 / 105 / 107 |
| developed 2023 | 149,975 | 6,158 | 0.041 | 2,848 / 2,746 / 2,846 | 117 / 113 / 117 |
| developed 2024 (immature) | 149,967 | 5,988 | 0.040 | 2,925 / 2,825 / 2,925 | 117 / 113 / 117 |
| emerging 2023 | 14,108 | 491 | 0.035 | 2,618 / 2,575 / 2,618 | 91 / 90 / 91 |
| emerging 2024 (immature) | 14,950 | 507 | 0.034 | 2,560 / 2,442 / 2,560 | 87 / 83 / 87 |

Frequency 15% lower, severity similar, burning cost 20% lower. Peril mix by cost: theft 43% / 51% vs 41–45%, flood 34% / 27% vs 23–27%, escape of water 15% / 13% vs 22–24%, accidental damage 8% vs 11%. Flood (86 claims) and escape of water (172) are thin.

## 5. Acquired-portfolio check (R-0407, R-0410)

No channel, product or segment flag identifies the 2025 broker book: channel mix is identical in 2024 and 2025. The training analogue is the **new-business segment** (`new_business = true`, 14% of training rows). Pre-registered table, emerging training years, frequency and burning cost capped at 25k, age-standardised to the renewal book's age mix:

| Line | New-business exposure | New-business claims | Raw frequency NB vs renewal | Age-standardised frequency relativity | Age-standardised capped-cost relativity | Persistence of 2023 NB into 2024 |
|---|---:|---:|---|---:|---:|---:|
| motor | 3,040 | 697 | 0.229 vs 0.177 | **1.17** | **1.24** | 1.00 (survivor extract) |
| buildings | 1,810 | 77 | 0.043 vs 0.045 | 0.97 | 1.18 | 1.00 |
| contents | 2,233 | 102 | 0.046 vs 0.033 | 1.25 | 1.33 | 1.00 |

New business is 17–25% worse than renewals after removing its younger age mix in motor and contents; buildings is flat on frequency and worse on cost but rests on 77 claims (not credible on its own). Declared history is identical across cohorts (`prior_claims_5y` mean 0.27, zero-claims share 77%, licence points 0.90 in 2025 joiners, 2023–24 joiners and earlier). The new-business age mix in training matches the test new-business age mix within 1–2 points per band, so the model is **interpolating on age and extrapolating on volume**: 876 new-business claims must carry a relativity that will be applied to 76% of the test book. The 2025 book cannot be assumed to behave like the renewal book; it should be priced at the new-business relativity, and the model's learned new-business effect must be compared with this table after fitting (R-0410). Persistence of first-year policies cannot be measured (100% by construction of the survivor extract).

## 6. Leakage checks

Adversarial validation and single-feature stamps: §2 above and profile §7. Columns whose distribution exists only in training: `customer_service_contacts` upper tail (max 20 vs 5), `renewal_decision` (absent from test), `customer_since_year ≤ 2024`, non-null `campaign_code` only for 2023+ joiners, and 2025 weather values (prediction-year environmental data, R-0022). All excluded from features; `missed_payments_12m` tested and kept (F-14).

## 7. Implications for modelling

- **Drop** as features: customer_since_year, campaign_code, customer_service_contacts, renewal_decision, yearly weather, compulsory_excess (constant), region/branch for any borrowed component (market-specific).
- **Keep as mix** and evaluate on the new-business subset: new_business, renewal_count, tenure_years, age band, years_licensed, ncb_years, marketing_segment, discount_applied (R-0406).
- **Re-estimate** from emerging data: line levels (motor 25% below developed, buildings cap-dependent, contents 20% below), frequency (motor 30% higher), motor severity (45% lower), peril mix, the new-business relativity (1.17–1.33), and the completion of 2024 (see target_notes).
- **Borrow** from the developed market with a stated sensitivity: the report-lag tail beyond 18 months (2.2% of motor cost, ≤ 0.2% home), the annual trend (motor −0.5%, buildings +6.5%, contents +4.9%), and shape relativities where emerging counts are thin (buildings perils, contents flood/escape of water), expressed on the common schema.
- **Watch**: the buildings level (fire-driven, three cut-offs disagree), the vehicle_age definition question, the 2023 survivor sample when validating 2023 → 2024 (the 2024 book includes lapses the 2023 book cannot), and the gender column (regulatory question before use).
- The acquired book's size (4× the 2024 exposure) means the 2025 line totals are set by the new-business relativity and the level, not by any feature refinement.
