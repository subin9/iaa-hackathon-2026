# Shift report — emerging market (2023-24 training, 2025 test) vs developed market (2021-24)

Evidence scripts: `work/p20_shift.py` (PSI, adversarial validation, acquired-book tables; output `work/p20_out.txt`, `work/shift_evidence.json`), `work/p21_adv_residual.py` (`work/adv_residual.json`), `work/p12_profile_stats.py` (frequency/severity tables). PSI uses nulls as their own bucket and reference-decile bins for numeric columns; the usual reading is < 0.1 stable, 0.1-0.25 moderate, > 0.25 large. All claim figures are raw at the valuation date 31 Dec 2024 (no IBNR adjustment) unless stated.

## 1. Schema differences

Summarised from `schema_mapping.md`. Only in developed: date_of_birth, credit_band, annual_mileage, telematics_opt_in, telematics_score, integer ages. Only in emerging: gender, age bands, expenses, reference_policies. Same name but different encoding: construction_type (11 raw codes → 4 levels), occupation (free text → 20 titles + self-employed flag), region (R01-R12 vs E01-E06, no correspondence), customer_since_year / campaign_code (cohort stamps in the emerging data). Same name, same encoding, different distribution: channel, vehicle_age, tenure, missingness level. Proposed common representation: age band (5), construction (4), occupation_base (20) + self_employed, tenure = renewal_count, market-specific region.

## 2. Emerging train vs emerging test (PSI, all three lines agree within ±0.03)

| rank | column | PSI motor / buildings / contents | what moved | interpretation |
|---|---|---|---|---|
| 1 | exposure | 2.43 / 2.15 / 2.69 | test rows start throughout January 2025 (0.96-0.99 exposure) and 2025 is one row per policy | (b) definition of the row window, not risk; exposure is an offset, not a feature |
| 2 | renewal_count | 1.92 / 1.92 / 1.94 | share at 0 rises from 14% to 76% | (a) portfolio mix: the acquired book; kept as tenure |
| 3 | campaign_code | 1.90 / 1.90 / 1.92 | null share falls from 81% to 17% | (c) time identity: null ⇔ joined before 2023; excluded |
| 4 | new_business | 1.86 / 1.85 / 1.88 | 14% → 76% | (a) mix; kept, the key segment of 2025 |
| 5 | customer_service_contacts | 0.14 / 0.06 / 0.03 | tail ≥ 3 shrinks from 9.5% to 0.8% (motor) | (c) leakage: in-period counts vs pre-period snapshot; excluded |
| 6 | marketing_segment | 0.08 / 0.08 / 0.07 | young_affluent 18% → 26%, senior_affluent 12% → 10% | (a) mix (younger book) |
| 7 | years_licensed (motor) | 0.08 | more 0-3 years | (a) mix, consequence of age |
| 8 | discount_applied | 0.06 / 0.06 / 0.05 | 0.10 share 0.7% → 3.8% | (b) commercial practice within comparison_site; excluded as redundant with channel |
| 9 | written_premium | 0.05 / 0.04 / 0.03 | top decile 10% → 15% / 13% / 13% | (a) mix (younger drivers, 2025 rate level); kept, see §7 |
| 10 | age band | 0.05 / 0.05 / 0.05 | 17-34 share 39% → 50%, 65+ 28% → 24% | (a) mix |
| — | everything else | < 0.012 | sum_insured, occupation, body_type, make_model, ncb_years, channel (identical 70/25/5), region, property and address columns all stable | no shift |

Nothing in the test files has a value range outside training except the smaller `customer_service_contacts` tail and `renewal_count` values 17 (18 rows). Channel, region, urban density, cover type, sum insured and all address attributes are stable: the acquired book was written in the same places on the same products.

## 3. Developed (training years 2021-24, harmonised) vs emerging training (2023-24)

Mapping applied before comparison: developed ages → bands, construction codes → 4 levels, exposure recomputed. Developed customer-level columns are compared on the 90% of developed motor rows whose customer exists (10% of developed motor policy rows reference a customer_id absent from the developed customers table; buildings and contents link 100%).

| column | PSI (motor / buildings / contents) | what differs | interpretation |
|---|---|---|---|
| region | 14.3 | disjoint code sets | definition: no shared geography; region relativities cannot be borrowed |
| channel | 1.13 / 1.11 / 1.12 | broker 25% → 70%, comparison_site 35% → 5%, direct 40% → 25% | mix: a broker-led market; channel relativities re-estimated |
| vehicle_age | 0.99 | emerging minimum 3 years, median 9 vs 7; no vehicles under 3 years | mix (older fleet) plus 12% nulls; relativity shape may differ at the young end, which the emerging data does not observe |
| discount_applied | 0.22 | consequence of channel | definition / redundant |
| the fifteen 12%-null columns (soil_type, occupation, distance_to_river_km, engine_size_cc, roof_type, marital_status, overnight_parking, years_at_address, household_size, energy_rating, days_unoccupied, smoke_alarms, security_level, high_value_items, vehicle_age) | 0.15-0.18 each | almost entirely the null bucket (2.5% → 12%); the non-null shares differ by ≤ 3 pts except soil_type clay 40% → 31% | data-definition (missingness) rather than risk; nulls kept as a level |
| tenure (contents) | 0.07 | renters 30% → 43% | mix |
| campaign_code | 0.09 | null 68% → 81% | cohort stamp in both; excluded |
| elevation_m | 0.05 | 0-60 m vs 0-197 m | mix / geography: flat, low-lying market |
| age band | 0.03 | emerging younger (17-24 20% vs 14%) and more 65+ (28% vs 31%) | mix |
| everything else (sum_insured, premium, excess, cover, body/fuel, ncb, licence points, prior claims, property attributes, payment, marketing columns) | < 0.03 | | stable: the product and underwriting footprint are the same |

The two markets are the same product written through a different channel mix in a different geography with an older fleet and more renters; the risk variables themselves are distributed alike. What differs is how the risk variables translate into claims (§4), which is the part that cannot be read off the distributions.

## 4. Frequency, severity and peril mix by line, per exposure-year (raw at 31 Dec 2024)

| line | market | year | exposure | claims | frequency | severity (net) | burning cost | open share |
|---|---|---|---|---|---|---|---|---|
| motor | developed | 2021 | 187,992 | 27,390 | 0.146 | 3,870 | 564 | 1% |
| motor | developed | 2022 | 199,699 | 29,725 | 0.149 | 3,932 | 585 | 2% |
| motor | developed | 2023 | 199,682 | 28,020 | 0.140 | 4,191 | 588 | 4% |
| motor | developed | 2024 | 199,786 | 25,864 | 0.130 | 3,506 | 454 | 21% |
| motor | emerging | 2023 | 18,865 | 3,557 | 0.189 | 2,295 | 433 | 4% |
| motor | emerging | 2024 | 20,104 | 3,491 | 0.174 | 2,204 | 383 | 20% |
| buildings | developed | 2021 | 140,783 | 6,204 | 0.0441 | 8,716 | 384 | 0.3% |
| buildings | developed | 2022 | 149,872 | 6,797 | 0.0454 | 9,059 | 411 | 0.8% |
| buildings | developed | 2023 | 149,987 | 6,824 | 0.0455 | 9,519 | 433 | 3% |
| buildings | developed | 2024 | 149,918 | 6,571 | 0.0438 | 10,250 | 449 | 25% |
| buildings | emerging | 2023 | 11,373 | 519 | 0.0456 | 11,269 | 514 | 4% |
| buildings | emerging | 2024 | 12,095 | 537 | 0.0444 | 6,909 | 307 | 25% |
| contents | developed | 2021 | 140,931 | 5,588 | 0.0397 | 2,665 | 106 | 0% |
| contents | developed | 2022 | 149,986 | 6,032 | 0.0402 | 2,662 | 107 | 0% |
| contents | developed | 2023 | 149,975 | 6,165 | 0.0411 | 2,848 | 117 | 0.3% |
| contents | developed | 2024 | 149,967 | 5,988 | 0.0399 | 2,925 | 117 | 13% |
| contents | emerging | 2023 | 14,108 | 491 | 0.0348 | 2,618 | 91 | 0% |
| contents | emerging | 2024 | 14,950 | 507 | 0.0339 | 2,560 | 87 | 12% |

Reading, using the mature years (developed 2021-23, emerging 2023):

- Motor: frequency is 30% higher in the emerging market (0.189 vs 0.145) and severity 43% lower (2,295 vs 3,990), so the burning cost is 25% lower (433 vs 580). The severity gap is in every peril (own damage 1,139 vs 1,856; third-party property 2,451 vs 3,681; bodily injury 10,702 vs 21,582; theft 4,134 vs 6,302; glass/hail 761 vs 1,086): a cost-level difference, consistent with lower repair and compensation costs, not a peril-mix effect. Peril mix: more glass/hail (19% vs 14% of claims) and third-party property (31% vs 30%), fewer own-damage claims (38% vs 44%); bodily injury is 6% of claims in both but 30% of cost against 38%. Credible: 3,557 claims in 2023.
- Buildings: frequency is the same (0.0456 vs 0.045); severity and burning cost cannot be compared on one year because the 2023 emerging figure is carried by fire (70 fire claims in two years = 45% of buildings cost; developed fire is 23%). Capping every claim at 100k, the emerging buildings burning cost is 408 (2023) and 273 (2024, raw at valuation) against 355-411 for the developed years on the same basis: 2023 sits at the developed level, 2024 well below it because fire claims halved (49 → 21) while storm and escape-of-water costs held. Peril mix differs materially: storm 44% of claims (developed 30%), escape of water 25% (38%), accidental damage 12% (15%), fire 7% (4%). Thin: 519 and 537 claims per year, 70 fire, 80 flood, 52 subsidence. A severity comparison by peril is not credible below ~300 claims; only storm and escape of water pass.
- Contents: frequency 15% lower (0.0348 vs 0.0403), severity the same (2,618 vs 2,725), burning cost 20% lower (91 vs 110). Peril mix: theft 41% of claims and 47% of cost (developed 32% / 42%), accidental damage 34% (38%), escape of water 17% (23%), flood 9% / 31% of cost (7% / 25%). Thin: ~500 claims per year; flood 86 claims.
- Reporting is faster in the emerging market in every line (cost-weighted share reported within 30 days: motor 60% vs 56%, buildings 91% vs 84%, contents 96% vs 94%), so a developed completion curve applied unchanged would over-gross-up the emerging latest year. Open-claim shares in 2024 are the same in both markets (motor 20-21%, buildings 25%, contents 12-13%).
- Open-claim reserving: in the developed market the mean incurred of open 2024 claims (motor 6,115; buildings 14,777) is far below open claims of earlier years (20-27k; 23-29k), the under-reserving pattern R-0105 warns about; it is examined for the emerging market in target_notes.md.

## 5. Acquired-portfolio check (R-0407)

The 2025 test book is 76% new business; the training data has 14% new business (6,535 / 3,786 / 4,716 rows; 3,040 / 1,810 / 2,233 exposure-years; 697 / 77 / 102 claims). Inside the training data:

| line | segment | exposure | claims | frequency | severity | burning cost | prior_claims_5y mean |
|---|---|---|---|---|---|---|---|
| motor | renewals | 35,929 | 6,351 | 0.177 | 2,200 | 389 | 0.266 |
| motor | new business | 3,040 | 697 | 0.229 | 2,703 | 620 | 0.268 |
| motor | new business, 2023 only | 1,210 | 315 | 0.260 | 3,455 | 900 | 0.276 |
| motor | new business, 2024 only | 1,830 | 382 | 0.209 | 2,082 | 435 | 0.262 |
| buildings | renewals | 21,658 | 979 | 0.0452 | 9,140 | 413 | 0.269 |
| buildings | new business | 1,810 | 77 | 0.0425 | 7,936 | 338 | 0.263 |
| contents | renewals | 26,825 | 896 | 0.0334 | 2,600 | 87 | 0.275 |
| contents | new business | 2,233 | 102 | 0.0457 | 2,486 | 114 | 0.270 |

- Motor new business runs 30% above renewals on frequency; standardised to the renewal book's frequency by age band (new business is younger) the excess is +18% (697 claims, credible to about ±8%). Policies that were new in 2023 still ran 9% above other renewals in 2024 (0.183 vs 0.168, 404 claims), so about half of the excess is selection that persists and half is a first-year effect. The 2023 new-business severity (3,455) is inflated by large claims; 2024 new-business severity (2,082) is below the renewal level.
- Buildings new business shows no frequency excess (ratio to age-standardised expectation 0.93) on 77 claims: not credible either way. Contents new business is +29% raw and +29% age-standardised on 102 claims, and 2023 new policies ran 25% above other renewals in 2024 (62 claims): suggestive, thin.
- Channel inside training: comparison-site rows have the highest motor frequency (0.200 vs broker 0.182, direct 0.174) and buildings frequency (0.050 vs 0.046 / 0.041); the test channel mix is unchanged, so this does not move the level.
- Tenure: frequency falls from tenure 0 to 3-7 years and is flat after (motor 0.229 → 0.180 → 0.173 → 0.178; contents 0.046 → 0.036 → 0.032 → 0.034); buildings flat.
- Declared history: prior_claims_5y mean is 0.26-0.28 in every segment (train renewals, train new business, test renewals, test new business); motor ncb_years mean 6.5 (train renewals), 5.5 (train new business), 5.7 (test new business); years_licensed 27.8 / 20.8 / 21.5. On everything declared, the acquired book looks like the insurer's own new business, slightly older in licence terms.
- Separability of the acquired book from the insurer's own new business on risk features (new-business rows only, time-identity and leakage columns removed): AUC 0.60 / 0.57 / 0.60, driven by previous_insurer (40 levels, likely noise) and occupation (more students in the acquired book). The 2025 book can be modelled as new business of the kind already in training; what the model extrapolates is the level of the new-business effect, estimated from 3,040 / 1,810 / 2,233 exposure-years and applied to 60,000 / 36,000 / 45,000 exposure-years. A ±10% error in the motor new-business relativity moves the motor test level by about ±7%; in buildings and contents the relativity is not credible at all and the modelled new-business effect should be shrunk toward the renewal level.

## 6. Leakage checks (R-0005, R-0006)

Adversarial validation, 2024 training rows vs 2025 test rows, LightGBM, 3-fold out-of-fold AUC:

| feature set | motor | buildings | contents |
|---|---|---|---|
| all candidate columns including customer_since_year | 1.000 | 1.000 | 1.000 |
| single customer_since_year | 0.882 | 0.881 | 0.882 |
| single campaign_code | 0.786 | 0.787 | 0.788 |
| single renewal_count / single new_business | 0.820 / 0.802 | 0.820 / 0.801 | 0.821 / 0.803 |
| without customer_since_year and campaign_code and the leakage columns (mix kept) | 0.830 | 0.823 | 0.831 |
| residual: also without new_business and renewal_count | 0.633 | 0.580 | 0.589 |
| residual without make_model | 0.676 | — | — |

Excluded as time identity: customer_since_year (2025 only in test), campaign_code (null ⇔ joined before 2023). Excluded as leakage: customer_service_contacts (grows with the claims in the row; training-only tail), renewal_decision (post-period outcome), discount_applied (redundant with channel, meaning changed), weather by calendar year (2025 values unknowable). Kept although they separate strongly: new_business and renewal_count — they are the acquired-book mix the model has to price, and they have the same meaning in every year. The residual AUC of 0.58-0.63 is the mix that remains after those: younger drivers with fewer licence years, more students, higher premiums in the top decile, and in motor a make_model term that is 300-level sampling noise (test/train share ratios 0.87-1.18 across codes, consistent with noise of ±8%); it is what the model must handle through its features, not a leak.

Columns whose distribution exists only in training: customer_service_contacts ≥ 6 (1.5% of motor training rows, 0 test rows), renewal_decision (whole column). No test column has values outside the training range.

## 7. Implications for modelling

- Drop: customer_since_year, campaign_code, customer_service_contacts, renewal_decision, discount_applied, compulsory_excess, calendar-year weather, region relativities from Part 1, make_model relativities from Part 1, all dq_flag_ columns.
- Re-estimate on emerging data: line levels (motor −25%, contents −20% vs developed on mature years; buildings undetermined by fire), channel relativities (broker-led market), the new-business / tenure effect (the single largest lever for 2025), vehicle_age shape (no vehicles under 3 years), severity by peril (every motor peril ~40-50% cheaper).
- Borrow with a stated sensitivity: the completion-curve tail beyond the 12-24 months observed, trend (one mature year cannot give one), severity shape for fire, flood and subsidence (70 / 80 / 52 claims), bodily-injury development.
- Keep and watch: written_premium (the insurer's own 2025 rating; its top decile grows in test), sum_insured after rescaling, age band (coarser than Part 1), ncb_years / years_licensed (inconsistent on 16-22% of rows, same in train and test).
- Evaluate every model on the new-business subset of training rows separately (R-0406); report the new-business level against the age-standardised +18% motor excess, and shrink buildings and contents new-business effects toward the renewal level because 77 and 102 claims cannot support a relativity.
- Expect the 2025 level to be driven by three things in order: the completion of 2024 and the trend assumption, the new-business relativity, and the fire/flood load in buildings. Each is quantified in target_notes.md and adaptation_decisions.md.
