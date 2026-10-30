# Schema mapping — developed (Part 1) ↔ emerging (Part 2)

Rule applied (R-0401): map to the coarsest representation both markets support; never invent precision the new market does not record. Columns not listed are identical in name, type, code list and meaning in both markets (verified column by column, level by level).

## 1. Columns only in one market

| Table | Column | Present in | Mapping to the common representation |
|---|---|---|---|
| customers | date_of_birth | developed | **Drop.** Emerging records age only as a band; derive `age_band` in the developed data from date of birth at period start and use the band in both (see §2). |
| customers | credit_band (A–E) | developed | **Drop** from any common model; no emerging equivalent (no proxy — `marketing_segment` affluent/mainstream/budget is a marketing tier, not credit). Listed as a lost feature. |
| customers | gender (F/M) | emerging | **Emerging-only feature.** Not in developed; can be used in an emerging-only model, cannot be borrowed. Flag for the team: whether gender may be used in pricing is a regulatory question for this market. |
| policies_motor, test_motor | driver_age (int) | developed | → `driver_age_band` with the emerging cut-points: 17–24, 25–34, 35–49, 50–64, 65+. Developed shares after banding: 14 / 17 / 19 / 19 / 31%. |
| policies_buildings/contents, tests | policyholder_age (int) | developed | → `policyholder_age_band`, same cut-points. |
| policies_motor, test_motor | driver_age_band (str) | emerging | kept as is (common representation). |
| policies_buildings/contents, tests | policyholder_age_band (str) | emerging | kept as is. |
| policies_motor, test_motor | annual_mileage | developed | **Drop**; no emerging equivalent. `vehicle_use` (social/commuting/business) is the only mileage proxy common to both. |
| policies_motor, test_motor | telematics_opt_in, telematics_score | developed | **Drop**; 12% opt-in in developed, nothing in emerging. |
| — | expenses, reference_policies | emerging | Reference tables, not features. `expenses` carries both markets' loadings (emerging `commission_comparison_site` null → team query F-22). `reference_policies` = 20 test rows stacked wide (F-23). |

## 2. Same name, different encoding or granularity

| Column | Developed | Emerging | Common representation |
|---|---|---|---|
| construction_type | free text with case/whitespace variants: `brick/Brick/BRICK`, `stone/STONE`, `non_standard/NON_STANDARD`, `W/w`, `T/t` (normalised shares 70 / 8 / 10 / 6 / 6%) | 4 codes `BRK / STN / MIX / WOD` (70 / 8 / 10 / 12%) | Emerging codes. Developed: lower-case+strip, then `brick→BRK`, `stone→STN`, `non_standard→MIX`, `w` and `t` (wood, timber) → `WOD`. Shares match to the percent, which supports the mapping; `WOD` loses the wood/timber distinction (coarser). |
| region | R01–R12 | E01–E06 | **No cross-market mapping** (different geographies). Keep `region` as a market-specific categorical; any borrowed relativity must be at the level of attributes that exist in both (`urban_density`, `flood_zone`, `elevation_m`, `soil_type`). |
| occupation | 20 clean title-case levels | 81 raw levels = the same 20 with case / trailing-space variants and a random "Self-employed " prefix | The developed 20-level list; emerging normalised to it in cleaning (F-16). |
| campaign_code | 15 codes; null for customers who joined ≤ 2020 | the same 15 codes; null for joined ≤ 2022 | Not a feature in either market (cohort stamp, F-12). |
| customer_since_year | 2006–2025 | 2008–2025 | Not a feature (stamp, F-11). Common derived quantity: `tenure_years = policy year − customer_since_year`, which has the same meaning in both markets and in train/test. |
| age (any) | integer | 5 bands | bands (above). Loss of precision inside the 17–24 and 65+ bands, where the developed market shows the steepest age curve. |
| vehicle_age | 0–28, 7% of rows < 3 years | 3–26, no vehicle under 3 years; distribution shifted ≈ +2 years (PSI 1.05) | Numeric in both. **Candidate definition difference** (age from first registration vs. from import?) or genuine portfolio difference (no new-car business). Treat as mix in the emerging model; do not borrow a developed relativity below age 3. Team query in the shift report. |
| exposure | stored, with day-count errors in both | stored, with day-count and 360-day errors | Recomputed from period dates (inclusive / 365) in both markets for every comparison. |
| sum_insured | ×1,000 errors on 0.2% of rows in both | ×1,000 errors on 0.2% of rows | Same proportional repair rule (log10(premium / sum insured) widest-gap boundary) in both. |
| missed_payments_12m, customer_service_contacts, days_quote_to_inception, discount_applied, renewal_count, new_business | same | same | identical meaning; `customer_service_contacts` excluded in both (claims-driven); `discount_applied` has a different level mix (developed 45% discounted, emerging 26%) — a pricing-practice difference, not an encoding one. |

## 3. Identical columns (kept as is)

policies: period_start, period_end, voluntary_excess, compulsory_excess (constant per line in both), channel (same 3 levels, very different mix), payment_method, written_premium, renewal_count, new_business, days_quote_to_inception, discount_applied; motor: years_licensed, ncb_years, vehicle_value_group (1–20), make_model (same 300 codes), engine_size_cc, body_type, transmission, seats, vehicle_colour, fuel_type, driver_assist, cover_type, overnight_parking, vehicle_use, named_young_driver; buildings: occupancy, days_unoccupied, smoke_alarms, accidental_damage_cover, mortgage; contents: tenure, security_level, high_value_items, accidental_damage_cover, works_from_home, lodgers, bicycle_cover; customers: marital_status, household_size, prior_claims_5y, licence_points, years_at_address, email_domain, marketing_consent, document_preference, previous_insurer (same 40 codes), branch_id (1–25), marketing_segment (same 12); addresses: urban_density, flood_zone (1–5, 2.9% null in both), distance_to_river_km, elevation_m (emerging max 60 m vs 197 m), soil_type, year_built, property_type, roof_type, basement, trees_within_5m, listed_building, bedrooms, energy_rating, solar_panels; weather: all 7 indices (same units; different climate); claims: all 12 columns, same 11 perils, same 3 statuses.

## 4. Consequences for borrowing

- Any relativity borrowed from Part 1 must be re-expressed on the banded age, the 4-code construction type and without credit band, mileage and telematics. Part 1 models that used `driver_age` as a continuous variable cannot be applied directly; a GBM retrained on the developed data with the common schema would be the vehicle for any borrowed shape.
- `region`, `branch_id` and `make_model`-level effects are market-specific and must be learned from emerging data or shrunk to the line level.
- The common feature set after mapping has 5 fewer motor columns and 2 fewer customer columns than Part 1 used, and one new column (gender) that Part 1 never saw.
