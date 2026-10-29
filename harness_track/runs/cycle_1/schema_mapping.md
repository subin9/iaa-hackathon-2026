# Schema mapping — developed (Part 1) ↔ emerging (Part 2)

Rule applied (R-0401): map to the coarsest representation both markets support; never invent precision the emerging market does not record. "Common" is the representation used in the modelling tables and in any model that borrows developed-market shape. Columns not listed below have the same name, type, encoding and meaning in both markets (checked value set by value set; see `work/p04_out.txt`).

## 1. Columns only in the developed data

| table | column | developed content | decision |
|---|---|---|---|
| customers | date_of_birth | date 1933-2007 | DROP from the common schema. The emerging market records only an age band on the policy; age is mapped the other way (section 3). |
| customers | credit_band | A-E | DROP. No emerging equivalent; a developed model that uses credit_band cannot be scored on emerging rows. |
| policies_motor, test_motor | annual_mileage | 0-86,000 | DROP. Not recorded in the emerging market. |
| policies_motor, test_motor | telematics_opt_in, telematics_score | 12% opt-in; score 1-100 | DROP. Not recorded. |
| policies_* | driver_age / policyholder_age | integer 17-91 | REPLACED by the band (section 3). |

## 2. Columns only in the emerging data

| table | column | emerging content | decision |
|---|---|---|---|
| customers | gender | F / M (50/50) | Emerging-only feature; usable within the emerging market, cannot be borrowed from Part 1. Flagged for the team: use is subject to the market's rating rules (team query in the retrospective). |
| policies_*, test_* | driver_age_band / policyholder_age_band | 17-24, 25-34, 35-49, 50-64, 65+ | Common age representation (section 3). |
| expenses | (table) | loadings by market | Used for the premium build, not for risk cost. |
| reference_policies | (table) | 20 test rows in a wide schema | Worked examples; mapped by `line` back to the line-specific test schema. |
| cleaned tables | dq_flag_* | booleans | Audit markers added by cleaning; never features (R-0011). |

## 3. Same name, different encoding, granularity or meaning

| column | developed | emerging | common representation and mapping |
|---|---|---|---|
| driver_age → driver_age_band; policyholder_age → policyholder_age_band | integer age | 5 bands | **Band.** developed age a → band: a ≤ 24 → '17-24'; 25-34 → '25-34'; 35-49 → '35-49'; 50-64 → '50-64'; ≥ 65 → '65+'. Developed band shares after mapping: 13.9 / 17.3 / 18.8 / 19.0 / 31.0%; emerging training 20 / 19 / 16 / 17 / 28%. Precision lost: within-band age slope (Part 1 used integer age). |
| construction_type | 11 raw codes: Brick, brick, BRICK (70%), non_standard, NON_STANDARD (10%), stone, STONE (8%), W, w (6%), T, t (6%) | BRK (70%), MIX (10%), STN (8%), WOD (12%) | **Four levels** brick / non_standard / stone / timber. Developed: {Brick, brick, BRICK} → brick; {stone, STONE} → stone; {W, w, T, t} → timber; {non_standard, NON_STANDARD} → non_standard. Emerging: BRK → brick; STN → stone; WOD → timber; MIX → non_standard. Evidence: the shares line up level by level (brick 70/70, stone 8/8, timber 12/12 = W+T, non_standard 10/10). The developed W/T split (wood vs timber frame) is not recoverable in the emerging coding, so it is collapsed. |
| occupation | 20 clean titles ('Care worker') | 80 raw strings: casing/whitespace variants of the same 20 titles plus 'Self-employed <title>' (10% of customers) | **occupation_base** (20 levels, developed spelling) + **self_employed** (bool, emerging only; developed = false/unknown). Cleaned customers.occupation keeps the normalised full string ('Self-employed care worker'); the modelling tables split it. |
| region | R01-R12 | E01-E06 | **No mapping.** Different geographies with no shared code; region is a market-specific categorical. Any developed relativity by region is dropped; emerging region effects must be estimated from emerging data (six levels, the smallest 4%). |
| customer_since_year | 2006-2025 | 2008-2025 | **Replace by tenure = renewal_count** (identical in meaning: period_year − customer_since_year on every row). customer_since_year itself is a calendar stamp and is excluded (F-14). |
| campaign_code | 15 codes, null 51% | 15 codes, null 20%; null for every customer who joined before 2023 and populated for every customer since | **Exclude.** In the emerging market it marks the join cohort (adversarial AUC 0.79 on its own), not a marketing effect. |
| discount_applied | 0 / 0.05 / 0.10 at 55 / 40 / 5% | same values, 74 / 25 / 1% in training; a deterministic function of channel | **Exclude as redundant** with channel; the 0.10 share within comparison_site changes between train and test (F-20). |
| exposure | years, with day-count rows (×365) in 1% of rows | years, with day-count (×365) and 360-day-basis (×365/360) rows | **Recomputed from dates** in both markets: (period_end − period_start + 1)/365, 4 dp. |
| sum_insured | CU, a few ×1000 rows | CU, ×1000 rows in buildings and contents (train and test) | **Rescaled** by the premium-ratio rule (F-03, F-04); same column after repair. |
| customer_service_contacts | 0-36 | 0-20 training, 0-5 test | **Exclude** (grows with in-period claims; training-only tail, F-16). |
| renewal_decision | 5 outcomes | 5 outcomes, training only | **Exclude** (post-period outcome, F-15). |
| flood_zone | 1-5, null 2.9% | 1-5, null 2.9% (missing not at random) | Same encoding; **null kept as an explicit 'unknown' level** in both. |
| weather.* | 2021-2025 by address | 2023-2025 by address | Same columns; **year-specific values not used**; if used, address mean over training years only (F-17). |
| channel | same 3 values | same 3 values | Same encoding; **mix differs** (broker 25% vs 70%). Kept; the relativity is re-estimated. |
| prior_claims_5y, licence_points, ncb_years, years_licensed, vehicle_value_group, voluntary_excess, compulsory_excess, payment_method, cover_type, body_type, fuel_type, transmission, seats, vehicle_colour, make_model, overnight_parking, vehicle_use, named_young_driver, driver_assist, occupancy, tenure, security_level, high_value_items, days_unoccupied, smoke_alarms, accidental_damage_cover, mortgage, works_from_home, lodgers, bicycle_cover, urban_density, soil_type, property_type, roof_type, energy_rating, basement, trees_within_5m, listed_building, bedrooms, solar_panels, year_built, elevation_m, distance_to_river_km, marital_status, household_size, years_at_address, email_domain, marketing_consent, document_preference, previous_insurer, branch_id, marketing_segment, missed_payments_12m, days_quote_to_inception, written_premium | identical value sets and types | identical | **AS-IS.** Distributions compared in the shift report; make_model has 300 codes in both markets with 0.2-0.4% each and the same code list, but there is no evidence the codes denote the same vehicles across markets, so make_model relativities are not borrowed. |

## 4. Claims

| column | developed | emerging | mapping |
|---|---|---|---|
| line, peril, status | identical vocabularies (3 lines, 11 perils, 3 statuses) | identical | AS-IS. Peril mix differs (shift report §4). |
| loss_date, report_date, paid_to_date, incurred_to_date, recoveries | same | same | AS-IS; net incurred = incurred_to_date − recoveries in both. |
| repairer_id, third_party_id | motor only / liability perils only | same | Not features (claim-level). |

## 5. Modelling-table representation (what the cleaned columns become)

- `exposure`: recomputed years. `completion`: row completion factor (target_notes.md). `offset = log(exposure × completion)` for training rows.
- Age: `age_band` (ordered categorical, 5 levels) in all three lines, from `driver_age_band` / `policyholder_age_band`.
- `construction_type` → 4 common levels; `occupation` → `occupation_base` + `self_employed`.
- `tenure` = `renewal_count`; `new_business` kept as delivered.
- Nulls kept; `flood_zone_cat` with an explicit 'unknown' level.
- Excluded from features (kept in modelling tables as `excl_*` columns for audit where useful): customer_since_year, campaign_code, discount_applied, customer_service_contacts, renewal_decision, compulsory_excess (constant), weather by year, all `dq_flag_*`.
- Columns that exist only in the developed market are not created in the emerging modelling tables; a developed model used for shape must be refitted on the common column set above.
