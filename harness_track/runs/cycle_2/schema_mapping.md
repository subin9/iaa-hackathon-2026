# Schema mapping — developed (Part 1) ↔ emerging (Part 2)

Rule applied: R-0401. Every table was diffed column by column (name, type, encoding, granularity, meaning). The
mapping targets the **coarsest representation both markets support**; nothing is invented for the market that does
not record it. "Emerging value" is the as-delivered value (after the cleaning in `outputs/cleaned/`, which only
normalises `occupation`, repairs `exposure` and `sum_insured`, and drops 36 claims).

## 1. Table-level differences

| Table | Developed | Emerging | Note |
|---|---|---|---|
| policies_motor | 979,968 rows, 2021–2024, 38 cols | 47,283 rows, 2023–2024, 36 cols | emerging lacks `annual_mileage`, `telematics_opt_in`, `telematics_score`; `driver_age` → `driver_age_band` |
| policies_buildings | 707,726 rows, 27 cols | 27,447 rows, 27 cols | `policyholder_age` → `policyholder_age_band` |
| policies_contents | 721,617 rows, 28 cols | 34,566 rows, 28 cols | `policyholder_age` → `policyholder_age_band` |
| test_* | 2025, 626,639 rows | 2025, 209,063 rows | same column differences as the policy tables; neither market has `renewal_decision` in test |
| customers | 545,240 rows, 18 cols | 135,856 rows, 17 cols | emerging has `gender` (new); lacks `date_of_birth` and `credit_band` |
| addresses | 575,983 rows, 16 cols | 136,914 rows, 16 cols | identical columns; `region` codes differ (R01–R12 vs E01–E06) |
| weather | 2021–2025, 7 indices | 2023–2025, same 7 indices | identical columns; different climate (see shift report) |
| claims | 163,150 rows, 12 cols | 9,258 rows (9,222 after cleaning), 12 cols | identical columns and code lists |
| expenses | — | 8 items × (developed, emerging, unit) | emerging only; carries both markets' loadings; one emerging value null |
| reference_policies | — | 20 rows, wide schema of all three lines | emerging only; exact copies of 20 test rows |
| sample_submission | 626,639 | 209,063 | identical structure |

## 2. Column-level mapping

### Columns only in the developed data → DROPPED for the common representation
| Column | Table | Treatment |
|---|---|---|
| `date_of_birth` | customers | Replaced by the age band carried on the policy row (see age mapping). Exact age is not recorded in the emerging market. |
| `credit_band` | customers | Not recorded in the emerging market; dropped. Part 1 relativities on credit band cannot transfer. |
| `annual_mileage` | policies_motor, test_motor | Not recorded; dropped. `vehicle_use` (social / commuting / business) is the closest shared proxy. |
| `telematics_opt_in`, `telematics_score` | policies_motor, test_motor | Not recorded (no telematics programme visible); dropped. |
| `driver_age`, `policyholder_age` (integer years) | policies_*, test_* | Mapped to the emerging band (below). |

### Columns only in the emerging data
| Column | Table | Treatment |
|---|---|---|
| `gender` (F/M, no nulls) | customers | Kept in the cleaned table; **excluded from the baseline features pending a regulatory decision** (findings F-GENDER). No developed counterpart, so a Part 1 relativity does not exist. |
| `driver_age_band`, `policyholder_age_band` | policies_*, test_* | Native representation; the developed ages are banded onto it. |
| `expenses` table | — | Premium-build inputs; not a model feature. |
| `reference_policies` table | — | Reference subset of test rows; not training data. |

### Same name, different encoding or granularity
| Column | Developed values | Emerging values | Common representation |
|---|---|---|---|
| age (`driver_age` / `policyholder_age` vs `*_age_band`) | integer 17–91 | `17-24`, `25-34`, `35-49`, `50-64`, `65+` | Band the developed age with the emerging cut points: <25 → 17-24; 25–34; 35–49; 50–64; ≥65 → 65+. Coarser than Part 1's continuous age; the Part 1 age curve has to be re-read at band midpoints or re-estimated. |
| `construction_type` | `Brick`/`brick`/`BRICK`, `stone`/`STONE`, `W`/`w`, `T`/`t`, `non_standard`/`NON_STANDARD` (11 raw spellings) | `BRK`, `STN`, `WOD`, `MIX` (4 clean codes) | 4 levels: **brick** ← {Brick, brick, BRICK, BRK}; **stone** ← {stone, STONE, STN}; **timber** ← {W, w, T, t, WOD}; **non_standard** ← {non_standard, NON_STANDARD, MIX}. Shares match across markets (brick 70% / 70%, non_standard-or-mixed 10% / 10%, stone 8% / 8%, W+T 12% / WOD 12%), which supports the pairing; the W vs T distinction of the developed data is not available in the emerging data and is collapsed. |
| `region` | R01–R12 (12 regions) | E01–E06 (6 regions) | **No mapping.** Regions are market-specific geography; `region` is a within-market categorical only. Developed relativities by region cannot transfer; the shared geographic signal must come from `urban_density`, `flood_zone`, `distance_to_river_km`, `elevation_m`, `soil_type`. |
| `occupation` | 20 clean titles | 81 raw spellings of the same 20 titles (case, trailing space, random "Self-employed " prefix) | The 20 developed titles. Emerging values normalised in the cleaned table (F-OCC-TEXT). |
| `customer_since_year` | 2006–2025 | 2008–2025, equals policy inception year; 73% of customers = 2025 | Time stamp in both markets (test cohort = 2025). Replace by **tenure = `renewal_count`** (identical content, same meaning in both years and markets). |
| `campaign_code` | null 51%, CMP00–CMP14 | null 20% (74.6% of pre-2025 customers, 0% of 2025 joiners) | Nullness is a join-year stamp in both markets; excluded from features in both. |
| `exposure` | year fraction with a day-count cluster (934 / 656 / 729 rows) | year fraction with a day-count cluster and a 360-day-basis cluster | Both recomputed as inclusive days / 365 from the period dates. |
| `sum_insured` | CU with ×1,000 cluster (1,395 / 1,402 train rows; 370 / 360 test rows) | CU with ×1,000 cluster (53 / 57 train; 104 / 135 test) | Same repair rule (premium / SI ratio a decade or more below the line median → ÷1,000). |
| `channel` | direct 40% / comparison 35% / broker 25% | broker 70% / direct 25% / comparison 5% | Same three codes, very different mix (modelled as mix, not mapped). |
| `discount_applied` | 0 / 0.05 / 0.10 | 0 / 0.05 / 0.10 | Same code list; in the emerging data it is a deterministic function of channel × new_business (redundant). |
| `renewal_decision` | 5 codes, training only | 5 codes, training only | Post-period outcome in both markets; excluded from features. |
| `customer_service_contacts` | count | count; 0 contacts ⇔ 0 claims | Leakage in both markets (R-0005); excluded. |
| `peril`, `status`, `line` (claims) | 11 perils, 3 statuses | same 11 perils, same 3 statuses | Identical code lists; peril-by-line mapping identical (motor 5, buildings 6, contents 4). |
| `flood_zone` | 1–5, null 2.9% | 1–5, null 2.9% | Identical; null kept as its own level in both (not at random in the emerging data). |
| all other shared columns (vehicle, cover, property, security, customer demographics, weather indices) | | | Identical names, types and code lists; no mapping needed. Distribution differences are reported in the shift report. |

### Type differences
| Column | Developed | Emerging | Note |
|---|---|---|---|
| `reference_policies.*` numeric columns | — | Float64 where the policy tables use Int64 (`years_licensed`, `ncb_years`, `vehicle_value_group`, `seats`) | Cross-line nulls in the wide schema; cast back to Int64 if the table is ever joined. |
| `household_size`, `high_value_items`, `days_unoccupied`, `vehicle_age`, `engine_size_cc` | Float64 | Float64 | Same (floats because of nulls) in both markets. |

## 3. Derived common feature set (what a cross-market model could use)

- Policy/risk: age band (5 levels), new_business, renewal_count (tenure), channel, payment_method, voluntary_excess,
  cover/product attributes (motor: years_licensed, ncb_years, vehicle_value_group, vehicle_age, make_model, engine_size_cc,
  body_type, transmission, seats, vehicle_colour, fuel_type, driver_assist, cover_type, overnight_parking, vehicle_use,
  named_young_driver; buildings: sum_insured, construction_type (4-level common coding), occupancy, days_unoccupied,
  smoke_alarms, accidental_damage_cover, mortgage; contents: sum_insured, tenure, security_level, high_value_items,
  accidental_damage_cover, works_from_home, lodgers, bicycle_cover).
- Customer: occupation (20 titles), marital_status, household_size, prior_claims_5y, licence_points, years_at_address.
- Address: urban_density, flood_zone (+unknown), distance_to_river_km, elevation_m, soil_type, year_built,
  property_type, roof_type, basement, trees_within_5m, listed_building, bedrooms, energy_rating, solar_panels.
- **Within-market only**: region, make_model (same 300 codes but market-specific vehicle populations), branch_id,
  previous_insurer, marketing_segment, email_domain.
- **Excluded in both markets**: renewal_decision, customer_service_contacts, customer_since_year, campaign_code,
  weather of the prediction year (year-specific), discount_applied (redundant), written_premium (own price; tested as a
  group only).
- **Emerging only, pending decision**: gender.

## 4. What the mapping loses

- Continuous age → 5 bands: the Part 1 young-driver curve is steep inside 17–24; the band cannot distinguish 17 from
  24. The emerging 17-24 band is 25% of test exposure, so this is the single largest loss of resolution.
- Credit band, mileage and telematics: Part 1 used them; no substitute exists. Their relativities are simply unavailable.
- W vs T construction: collapsed to timber.
- Region: no common geography; cross-market models must rely on the physical address attributes.
