# Modelling tables — column dictionary

One row per policy row of the cleaned tables, training (2023-2024) and test (2025), per line: motor 137,804 rows (47,283 train / 90,521 test), buildings 79,742 (27,447 / 52,295), contents 100,813 (34,566 / 66,247). Built by `work/p30_target.py` from `./outputs/cleaned/`.

## Keys, split and target columns (never features)

| column | meaning |
|---|---|
| row_id, policy_id, customer_id, address_id | identifiers as delivered |
| split | 'train' / 'test' |
| year | calendar year of period_start (2023, 2024, 2025) |
| period_start, period_end | as delivered |
| exposure | years, recomputed from dates (F-01/F-02) |
| completion | row completion factor at 31 Dec 2024 (target_notes §3); 1.0 for test rows |
| completion_alt | same with no borrowed tail beyond 540 days (sensitivity) |
| trend_factor | (1 + trend)^(2025 − year): 1.0609 / 1.03 (motor), 1.1236 / 1.06 (buildings), 1.1025 / 1.05 (contents) for 2023 / 2024; 1.0 for test |
| y | target: net incurred of linked claims at the valuation date; null for test |
| y_capped | y capped at the line's 99th percentile of positive y; line multipliers 1.0773 / 1.1200 / 1.0482 restore the total |
| n_claims, n_open, open_incurred, max_claim | claim counts and amounts behind y (audit; not features) |

Offset for a Tweedie model on y (or y_capped × multiplier): log(exposure × completion / trend_factor). Predictions for test rows = rate × exposure (completion 1, trend 1). Predictions for 2024 rows on the observed basis = rate × exposure × completion / trend_factor.

## Risk features (usable)

- Policy: age_band (5 bands, from driver_age_band / policyholder_age_band), voluntary_excess, channel, payment_method, missed_payments_12m, new_business, tenure_years (= renewal_count; 0 for new business), days_quote_to_inception, written_premium (annual premium as rated by the insurer).
- Motor only: years_licensed, ncb_years, vehicle_value_group, vehicle_age, make_model (300 codes), engine_size_cc, body_type, transmission, seats, vehicle_colour, fuel_type, driver_assist, cover_type, overnight_parking, vehicle_use, named_young_driver.
- Buildings only: sum_insured (rescaled, F-03), construction_type mapped to brick / stone / timber / non_standard, occupancy, days_unoccupied, smoke_alarms, accidental_damage_cover, mortgage.
- Contents only: sum_insured (rescaled, F-04), tenure (owner / renter), security_level, high_value_items, accidental_damage_cover, works_from_home, lodgers, bicycle_cover.
- Customer: gender (emerging only; use subject to the market's rating rules, open decision), occupation_base (20 titles), self_employed, marital_status, household_size, prior_claims_5y, licence_points, years_at_address, email_domain, marketing_consent, document_preference, previous_insurer, branch_id, marketing_segment.
- Address: region (E01-E06), urban_density, flood_zone (numeric, null kept) and flood_zone_cat ('1'-'5' / 'unknown', F-13), distance_to_river_km, elevation_m, soil_type, year_built, property_type, roof_type, basement, trees_within_5m, listed_building, bedrooms, energy_rating, solar_panels.
- Weather: wx_mean_* = address mean over 2023-2024 of hail_days, wind_exposure_index, freezing_days, dry_summer_index, wildfire_index, rainfall_mm, mean_temperature_c. No calendar-year values (F-17). Part 1 found weather features hurt; off by default.
- Nulls are kept as delivered (about 12% in fifteen columns, MCAR, F-12).

## Excluded columns (kept for audit, prefix excl_; not features)

excl_customer_since_year (time stamp, F-14), excl_campaign_code (join-cohort marker), excl_discount_applied (function of channel, meaning changed, F-20), excl_customer_service_contacts (grows with in-period claims, F-16), excl_renewal_decision (post-period outcome, training only, F-15), excl_compulsory_excess (constant per line).

## Flags and segment markers (not risk factors, R-0011)

dq_flag_exposure_repaired, dq_flag_sum_insured_rescaled, dq_flag_occupation_normalised (from cleaning), dq_flag_large_loss_capped (y above the cap), seg_post_mid_term_change (row follows another row of the same policy in the same year; the segment Part 1 found over-predicted, R-0309 — report on it, do not fit to it).
