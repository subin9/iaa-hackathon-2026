# Shift report — emerging market

Valuation date 31 December 2024 throughout. Emerging numbers use the cleaned tables (`outputs/cleaned/`);
developed numbers use `./data/developed/` with exposure recomputed from the period dates and the same claim linkage.
Statistics: `work/p20_shift.py` (PSI, adversarial validation), `work/p07_freq_sev.py` (frequency / severity).
PSI is computed on 10 quantile bins for numeric columns and on category shares for categoricals, nulls as a level.
Reading guide used: PSI < 0.1 stable, 0.1–0.25 moderate, > 0.25 large.

## 1. Schema differences

See `schema_mapping.md` for the full column-level mapping. In one paragraph: the emerging data drops
`date_of_birth`, `credit_band`, `annual_mileage`, `telematics_opt_in`, `telematics_score`, replaces integer age by
five age bands, adds `gender`, uses six region codes with no correspondence to the twelve developed ones, uses four
clean construction codes where the developed data had eleven spellings, and brings two new tables (`expenses`,
`reference_policies`). Claims columns and code lists are identical. All other shared columns have identical names,
types and code lists; their differences are distributional and are what the rest of this report is about.

## 2. Emerging train vs emerging test

Full PSI table, every shared column, sorted by the largest train→test shift (train = 2023–2024 rows, test = 2025 rows; dev→emerging compares developed 2021–2024 rows with emerging training rows; blank = column not comparable):

| column | motor train→test | buildings train→test | contents train→test | motor dev→emerging | buildings dev→emerging | contents dev→emerging | null train / test (motor) |
|---|---|---|---|---|---|---|---|
| customer_since_year | 7.930 | 7.918 | 7.947 | 1.321 | 0.673 | 0.671 | 0.0% / 0.0% |
| renewal_count | 2.017 | 2.019 | 2.045 | 0.183 | 0.183 | 0.187 | 0.0% / 0.0% |
| campaign_code | 1.899 | 1.900 | 1.921 | 0.052 | 0.093 | 0.097 | 80.6% / 17.3% |
| new_business | 1.857 | 1.854 | 1.878 | 0.000 | 0.001 | 0.001 | 0.0% / 0.0% |
| customer_service_contacts | 0.288 | 0.057 | 0.035 | 0.006 | 0.001 | 0.001 | 0.0% / 0.0% |
| exposure | 0.057 | 0.062 | 0.261 | 0.005 | 0.007 | 0.006 | 0.0% / 0.0% |
| marketing_segment | 0.078 | 0.078 | 0.074 | 0.752 | 0.051 | 0.055 | 0.0% / 0.0% |
| years_licensed | 0.076 |  |  | 0.049 |  |  | 0.0% / 0.0% |
| discount_applied | 0.057 | 0.055 | 0.054 | 0.220 | 0.224 | 0.219 | 0.0% / 0.0% |
| written_premium | 0.053 | 0.040 | 0.027 | 0.035 | 0.068 | 0.025 | 0.0% / 0.0% |
| policyholder_age_band |  | 0.052 | 0.050 |  | 0.034 | 0.036 |  |
| driver_age_band | 0.051 |  |  | 0.034 |  |  | 0.0% / 0.0% |
| ncb_years | 0.013 |  |  | 0.054 |  |  | 0.0% / 0.0% |
| sum_insured |  | 0.012 | 0.002 |  | 0.005 | 0.021 |  |
| body_type | 0.010 |  |  | 0.004 |  |  | 0.0% / 0.0% |
| occupation | 0.009 | 0.009 | 0.008 | 0.006 | 0.174 | 0.165 | 12.0% / 12.2% |
| make_model | 0.009 |  |  | 0.012 |  |  | 0.0% / 0.0% |
| years_at_address | 0.005 | 0.005 | 0.006 | 0.006 | 0.065 | 0.066 | 11.9% / 11.9% |
| marital_status | 0.003 | 0.003 | 0.002 | 0.004 | 0.162 | 0.162 | 12.1% / 11.9% |
| vehicle_age | 0.003 |  |  | 0.411 |  |  | 11.9% / 12.2% |
| previous_insurer | 0.002 | 0.003 | 0.003 | 0.705 | 0.003 | 0.003 | 0.0% / 0.0% |
| vehicle_value_group | 0.003 |  |  | 0.003 |  |  | 0.0% / 0.0% |
| engine_size_cc | 0.001 |  |  | 0.084 |  |  | 12.2% / 12.2% |
| household_size | 0.001 | 0.000 | 0.000 | 0.002 | 0.166 | 0.159 | 11.6% / 11.8% |
| cover_type | 0.001 |  |  | 0.007 |  |  | 0.0% / 0.0% |
| elevation_m | 0.000 | 0.001 | 0.000 | 0.022 | 0.020 | 0.021 | 0.0% / 0.0% |
| energy_rating | 0.000 | 0.001 | 0.000 | 0.152 | 0.158 | 0.151 | 11.8% / 12.1% |
| named_young_driver | 0.001 |  |  | 0.000 |  |  | 0.0% / 0.0% |
| days_quote_to_inception | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| bedrooms | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.0% / 0.0% |
| year_built | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 0.0% / 0.0% |
| days_unoccupied |  | 0.000 |  |  | 0.074 |  |  |
| voluntary_excess | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.0% / 0.0% |
| distance_to_river_km | 0.000 | 0.000 | 0.000 | 0.070 | 0.069 | 0.066 | 12.3% / 12.0% |
| listed_building | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| prior_claims_5y | 0.000 | 0.000 | 0.000 | 0.707 | 0.005 | 0.004 | 0.0% / 0.0% |
| high_value_items |  |  | 0.000 |  |  | 0.153 |  |
| soil_type | 0.000 | 0.000 | 0.000 | 0.172 | 0.181 | 0.181 | 12.0% / 11.9% |
| branch_id | 0.000 | 0.000 | 0.000 | 0.079 | 0.000 | 0.000 | 0.0% / 0.0% |
| document_preference | 0.000 | 0.000 | 0.000 | 0.702 | 0.000 | 0.000 | 0.0% / 0.0% |
| flood_zone | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.001 | 2.8% / 2.9% |
| payment_method | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| region | 0.000 | 0.000 | 0.000 | 14.297 | 14.303 | 14.300 | 0.0% / 0.0% |
| tenure |  |  | 0.000 |  |  | 0.074 |  |
| accidental_damage_cover |  | 0.000 | 0.000 |  | 0.000 | 0.000 |  |
| mortgage |  | 0.000 |  |  | 0.000 |  |  |
| email_domain | 0.000 | 0.000 | 0.000 | 0.702 | 0.000 | 0.000 | 0.0% / 0.0% |
| vehicle_colour | 0.000 |  |  | 0.000 |  |  | 0.0% / 0.0% |
| channel | 0.000 | 0.000 | 0.000 | 1.130 | 1.113 | 1.119 | 0.0% / 0.0% |
| gender | 0.000 | 0.000 | 0.000 |  |  |  | 0.0% / 0.0% |
| basement | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| missed_payments_12m | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| fuel_type | 0.000 |  |  | 0.086 |  |  | 0.0% / 0.0% |
| urban_density | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 | 0.0% / 0.0% |
| smoke_alarms |  | 0.000 |  |  | 0.155 |  |  |
| roof_type | 0.000 | 0.000 | 0.000 | 0.163 | 0.159 | 0.157 | 12.1% / 11.8% |
| seats | 0.000 |  |  | 0.000 |  |  | 0.0% / 0.0% |
| licence_points | 0.000 | 0.000 | 0.000 | 0.702 | 0.000 | 0.000 | 0.0% / 0.0% |
| trees_within_5m | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| marketing_consent | 0.000 | 0.000 | 0.000 | 0.702 | 0.000 | 0.000 | 0.0% / 0.0% |
| property_type | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| lodgers |  |  | 0.000 |  |  | 0.000 |  |
| overnight_parking | 0.000 |  |  | 0.161 |  |  | 12.0% / 12.0% |
| solar_panels | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |
| security_level |  |  | 0.000 |  |  | 0.165 |  |
| vehicle_use | 0.000 |  |  | 0.000 |  |  | 0.0% / 0.0% |
| construction_type |  | 0.000 |  |  | 0.000 |  |  |
| driver_assist | 0.000 |  |  | 0.000 |  |  | 0.0% / 0.0% |
| transmission | 0.000 |  |  | 0.000 |  |  | 0.0% / 0.0% |
| occupancy |  | 0.000 |  |  | 0.000 |  |  |
| bicycle_cover |  |  | 0.000 |  |  | 0.000 |  |
| works_from_home |  |  | 0.000 |  |  | 0.000 |  |
| compulsory_excess | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0% / 0.0% |

Interpretation of the shifts (train 2023–24 → test 2025):

| Column | PSI (motor / buildings / contents) | Type | Reading |
|---|---|---|---|
| customer_since_year | 7.9 / 7.9 / 7.9 | (c) time/identity | 73% of test customers carry 2025; the value is the join year. Excluded. |
| campaign_code | 1.9 / 1.9 / 1.9 | (c) time/identity | nullness flips from 75% to 0% between cohorts. Excluded. |
| new_business, renewal_count | 1.9 / 1.9 / 1.9 and 2.0 / 2.0 / 2.0 | (a) portfolio mix | new business 12–15% of training rows, 76% of test rows; renewal_count 0 for all of them. Both have the same meaning in both years and are the drivers the model must carry (R-0406, R-0410). Kept. |
| customer_service_contacts | 0.29 / 0.06 / 0.04 | (c) leakage | training-only upper tail; tied to claims. Excluded. |
| exposure | 0.06 / 0.06 / 0.26 | (a) mix | test rows are mostly January inceptions (exposure 0.9–1.0) and no 2-row years for new business; contents has more partial rows. Handled by the offset. |
| marketing_segment | 0.08 / 0.08 / 0.07 | (a) mix | the broker book is more "young_affluent" (26% → 32%). Marketing group excluded from the lean set anyway. |
| age band | 0.05 / 0.05 / 0.05 | (a) mix | 17-24 and 25-34 rise from 19–20% to 25% of exposure each; 65+ falls from 29% to 24%. Modelled. |
| years_licensed, ncb_years | 0.08 / – / – | (a) mix | younger book → fewer licence years (median 13 vs 24), more ncb 0–2. Modelled. |
| discount_applied | 0.06 / 0.06 / 0.05 | (b) definition | redundant with channel × new_business; the 0.10 level grows with new business. Excluded. |
| written_premium | 0.05 / 0.04 / 0.03 | (a) mix | test premiums 7% higher (younger drivers). Own price; tested as a feature group only. |
| everything else | < 0.02 | stable | channel mix identical (70/25/5), region, vehicle, property, security, customer demographics and null shares all stable between train and test. |

The broker book therefore differs from the training book in **tenure (all new), age (younger) and the attributes that
follow from age** — not in channel, geography, vehicle or property mix.

## 3. Developed vs emerging (training years)

Largest PSI developed → emerging (shared columns):

| Column | PSI (motor / buildings / contents) | Reading |
|---|---|---|
| region | 14.3 | different code lists: no overlap at all (definition). |
| channel | 1.13 / 1.11 / 1.12 | broker 25% → 70%, comparison_site 35% → 5% (mix). |
| customer_since_year | 1.32 / 0.67 / 0.67 | stamp in both markets. |
| marketing_segment | 0.75 / 0.05 / 0.06 | motor customers more "young_affluent"/"young_mainstream"; motor book skews young. |
| prior_claims_5y, previous_insurer, document_preference, email_domain, licence_points, marketing_consent (motor only) | ≈ 0.70 | **binning artefact of the motor comparison** (the developed customer join leaves the same set of nulls / levels but the quantile bins land differently); the category shares themselves differ by < 3 points. Not a real shift. |
| vehicle_age | 0.41 (motor) | emerging vehicles older (median 9 vs developed 7). |
| discount_applied, renewal_count | 0.22 / 0.18 | follows channel and tenure mix. |
| soil_type, occupation, household_size, marital_status, roof_type, energy_rating | 0.16–0.18 (property lines) | ~12% nulls in the emerging data vs ~2.5% developed (null level counts as a shift); the non-null shares are within 5 points, except soil clay 31% vs 41%. |
| fuel_type | small | electric 2% vs 8%. |
| age band | motor 17-24 20% vs 13%; 65+ 28% vs 31% | younger emerging book. |

Mix vs risk behaviour: channel, age, tenure, vehicle age and the null rate are mix (modelled or neutral). The
different claim levels in section 4 are **risk behaviour** that no shared column explains.

## 4. Frequency, severity and peril mix by line (raw at the valuation date, no IBNR adjustment)

| Line | Year | Market | Exposure | Claims | Frequency | Avg net | Burning cost | Burning cost, claims capped at 50k |
|---|---|---|---|---|---|---|---|---|
| motor | 2023 | emerging | 18,865 | 3,557 | 0.189 | 2,295 | 432.7 | 419.3 |
| motor | 2024 | emerging | 20,104 | 3,491 | 0.174 | 2,204 | 382.7 | 375.2 |
| motor | 2021 | developed | 187,992 | 27,356 | 0.146 | 3,871 | 563.3 | 521.7 |
| motor | 2022 | developed | 199,699 | 29,691 | 0.149 | 3,931 | 584.5 | 539.1 |
| motor | 2023 | developed | 199,682 | 27,990 | 0.140 | 4,191 | 587.5 | 495.9 |
| motor | 2024 | developed | 199,786 | 25,864 | 0.129 | 3,506 | 453.8 | 435.0 |
| buildings | 2023 | emerging | 11,373 | 519 | 0.046 | 11,269 | 514.3 | 348.1 |
| buildings | 2024 | emerging | 12,095 | 537 | 0.044 | 6,909 | 306.7 | 242.3 |
| buildings | 2021 | developed | 140,783 | 6,195 | 0.044 | 8,725 | 383.9 | 316.6 |
| buildings | 2022 | developed | 149,872 | 6,792 | 0.045 | 9,059 | 410.5 | 336.4 |
| buildings | 2023 | developed | 149,987 | 6,817 | 0.045 | 9,510 | 432.3 | 356.3 |
| buildings | 2024 | developed | 149,918 | 6,571 | 0.044 | 10,250 | 449.3 | 363.2 |
| contents | 2023 | emerging | 14,108 | 491 | 0.035 | 2,618 | 91.1 | 91.1 |
| contents | 2024 | emerging | 14,950 | 507 | 0.034 | 2,560 | 86.8 | 86.7 |
| contents | 2021 | developed | 140,931 | 5,583 | 0.040 | 2,663 | 105.5 | 105.3 |
| contents | 2022 | developed | 149,986 | 6,024 | 0.040 | 2,663 | 106.9 | 106.9 |
| contents | 2023 | developed | 149,975 | 6,158 | 0.041 | 2,848 | 116.9 | 116.0 |
| contents | 2024 | developed | 149,967 | 5,988 | 0.040 | 2,925 | 116.8 | 116.0 |

2024 is incomplete in both markets (emerging motor 83% complete on the cost-weighted curve, buildings 94%, contents
97%; see target_notes.md), so 2024 rows understate the ultimate level.

- **Motor**: frequency is 30% higher in the emerging market (0.19 vs 0.14) and severity 40% lower (2,250 vs 3,900);
  the net burning cost is 25% lower (433 vs 575 for mature years). Cost or compensation levels differ, not just mix.
  Third-party property severity 2,450 vs 3,680, bodily injury 10,700 vs 21,600, own damage 1,140 vs 1,860.
- **Buildings**: frequency identical (0.045). Severity is dominated by fire: 70 fire claims (6.6% of claims) carry
  45% of cost at 62,000 average vs 23% and 51,700 in the developed market; storm is more frequent (44% vs 30% of
  claims) and cheaper. With claims capped at 50k the burning costs are 348 / 242 (emerging) vs 317–363 (developed):
  the like-for-like level is the same order as the developed market, and the emerging 2023 vs 2024 gap is mostly
  nine fire losses above 100k in 2023. **Thin**: fire 70 claims, flood 80, subsidence 52.
- **Contents**: frequency 15% lower (0.034 vs 0.040), severity similar (2,600 vs 2,700–2,900), burning cost 20%
  lower (90 vs 107–117). Theft dominates both markets; flood is 31% of emerging cost from 86 claims (thin).

Peril mix (share of claims, emerging vs developed): motor own_damage 38% vs 44%, third_party_prop 31% vs 30%,
glass_hail 19% vs 14%, bodily_injury 6% vs 7%, theft 6% vs 6%; buildings storm 44% vs 30%, escape_of_water 25% vs
38%, accidental 12% vs 15%, flood 8% vs 8%, fire 7% vs 4%, subsidence 5% vs 5%; contents theft 41% vs 32%,
accidental 34% vs 38%, escape_of_water 17% vs 23%, flood 9% vs 7%. More hail (glass_hail) and storm, less water
damage: consistent with the warmer, wetter, hail-prone climate in the weather table.

## 5. Acquired-portfolio / new-business check (R-0407, R-0410)

Inside the emerging training data (both years, claims raw at valuation):

| Line | Segment | Exposure | Claims | Frequency | Burning cost | Freq ratio NB/renewal (raw) | Age-standardised freq ratio | Age-standardised burn ratio |
|---|---|---|---|---|---|---|---|---|
| motor | renewal | 35,929 | 6,351 | 0.177 | 389 | | | |
| motor | new business | 3,040 | 697 | 0.229 | 620 | 1.30 | **1.17** | **1.45** |
| buildings | renewal | 21,658 | 979 | 0.045 | 413 | | | |
| buildings | new business | 1,810 | 77 | 0.043 | 338 | 0.94 | 0.97 | 0.85 |
| contents | renewal | 26,825 | 896 | 0.033 | 87 | | | |
| contents | new business | 2,233 | 102 | 0.046 | 114 | 1.37 | **1.25** | **1.28** |

Developed market for reference (age-standardised): motor 1.22 (burn 1.18), buildings 1.10 (1.09), contents 1.12
(0.96). New business is worse than renewals in both markets; in the emerging data the motor cost excess (+45%) is
larger than its frequency excess (+17%), i.e. new-business claims are also bigger. Buildings new business is 77 claims:
its ratio below 1 is not credible evidence of a better segment.

By channel (emerging, freq / burn): motor broker 0.182 / 406, direct 0.174 / 384, comparison 0.200 / 537; buildings
0.046 / 419, 0.041 / 382, 0.050 / 374; contents 0.034 / 91, 0.035 / 84, 0.041 / 80. Broker business is not
distinguishable from direct on frequency; comparison-site business is worse but thin (1,900 / 1,200 / 1,500
exposure-years).

Declared history of the acquired book (test vs training customers): prior_claims_5y 0 / 1 / 2+ = 77 / 20 / 3% in both;
licence_points 80 / 12 / 6 / 2% in both; so the broker book does not declare a different history.

Persistence of first-year policies: 100% of 2023 new business reappears in 2024 (as does 100% of all 2023 policies —
the 2023 year is a survivor sample, so persistence cannot be measured on it); 85% of 2024 policies reappear in 2025.

**Can the 2025 book be assumed to behave like the renewal book?** No. The training new-business segment is 3,040 /
1,810 / 2,233 exposure-years (697 / 77 / 102 claims) against a test book of 60,700 / 36,400 / 45,400 new-business
exposure-years. The model extrapolates a segment that is 8% of training exposure to 77% of test exposure, with a
younger age mix than any training segment. The pre-model new-business relativities above (motor ×1.17 frequency,
×1.45 cost; contents ×1.25 / ×1.28; buildings ≈ 1 but thin) are the figures the model's own new-business relativity
must be compared with after fitting (R-0410).

## 6. Leakage checks

Adversarial validation, 2024 training rows vs 2025 test rows, 5-fold gradient boosting (R-0006), after the
cohort-stamp cross-tabulation of R-0016:

| Line | All columns | After removing stamps | Lean risk features only |
|---|---|---|---|
| motor | 1.000 | 0.846 | 0.649 |
| buildings | 1.000 | 0.810 | 0.571 |
| contents | 1.000 | 0.816 | 0.565 |

Single-feature AUCs above 0.80: customer_since_year 0.88, renewal_count 0.81, new_business 0.80, campaign_code 0.79
(just below), then nothing above 0.57. customer_since_year and campaign_code are stamps and are excluded.
new_business and renewal_count separate the years because the test year *is* new business, not because they are
time stamps: they take the same values with the same meaning in both years and are kept (R-0406). With only risk
features the residual AUC of 0.57–0.65 is portfolio mix (age band, licence years, ncb years, marketing segment), which
section 2 explains and the model is expected to carry.

Columns whose distribution exists only in training: renewal_decision (absent from test), customer_service_contacts
upper tail (max 20 vs 5). Both excluded. missed_payments_12m and days_quote_to_inception have identical train/test
distributions and weak claim correlation; they are kept out of the lean set and tested as a group.
weather 2025 is present for all test addresses and differs from 2023–24: year-specific values for the prediction year,
excluded from the lean set.

## 7. Implications for modelling

- **Drop**: customer_since_year, campaign_code, renewal_decision, customer_service_contacts, discount_applied, the
  2025 weather (and weather generally in the lean set), written_premium from the lean set.
- **Re-estimate on emerging data**: every level (base rate by line, new-business relativity, age-band relativities,
  channel, region, vehicle and property relativities). Motor runs at higher frequency / lower severity than the
  developed market, buildings fire is twice the cost share, contents is 20% cheaper: Part 1 levels do not transfer.
- **Borrow**: the report-lag tail beyond one year (emerging data observe at most 24 months), a trend range (one
  mature emerging year cannot give a trend), and the shape of thin-peril severity (fire, flood, subsidence, bodily
  injury) if a peril model is ever built.
- **Model the new-business effect explicitly** (new_business + renewal_count as features; evaluate on the
  new-business subset) and compare the fitted relativity with the pre-model figures in section 5.
- **Watch**: the 2023 survivor bias (the primary validation fold trains on survivors only); the buildings level, which
  swings 40% between years on a handful of fire losses (cap and redistribute, R-0104; quote credibility); the younger
  test age mix, where the 17-24 band is 25% of exposure and carries the steepest relativity.
- **Region** is market-specific: no cross-market pooling by region; use physical address attributes if pooling.
- **Gender** is available and strongly predictive in motor; its use is a team decision, not a modelling one.
