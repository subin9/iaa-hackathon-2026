# Schema mapping — developed (Part 1) ↔ emerging (Part 2)

Rule applied (R-0401): map to the coarsest representation both markets support; never invent
precision the new market does not record. "Common" is the representation a joint or borrowed model
must use. Columns not listed below are identical in name, type, code list and meaning in both markets
(verified by code-list comparison and PSI < 0.2 on non-null values; see shift_report.md §3).

## 1. Columns only in the developed data

| Table | Column | Role in Part 1 | Treatment for Part 2 |
|---|---|---|---|
| policies_motor / test_motor | `driver_age` (int) | risk factor | replaced by `driver_age_band` (see §3) |
| policies_buildings, policies_contents (+tests) | `policyholder_age` (int) | risk factor | replaced by `policyholder_age_band` |
| policies_motor / test_motor | `annual_mileage` | risk factor | **not available** — any Part 1 relativity on mileage cannot be borrowed; `vehicle_use` is the nearest proxy |
| policies_motor / test_motor | `telematics_opt_in`, `telematics_score` | risk factor (12% opt-in) | not available; drop |
| customers | `date_of_birth` | source of age | not available; age exists only as a band |
| customers | `credit_band` (A–E) | risk / payment factor | not available; `missed_payments_12m` and `payment_method` are the only payment-behaviour signals |

## 2. Columns only in the emerging data

| Table | Column | Content | Treatment |
|---|---|---|---|
| customers | `gender` (F/M, 50/50) | new attribute, no developed counterpart | usable feature for the emerging model only; check local regulation before pricing on it (team query) |
| policies_* / test_* | `driver_age_band`, `policyholder_age_band` | 17-24 / 25-34 / 35-49 / 50-64 / 65+ | the common age representation (§3) |
| — | `expenses` table | fixed/variable expense, commissions, premium tax, cat reinsurance, profit margin for both markets | premium build only; comparison-site commission null for emerging (F-17) |
| — | `reference_policies` table | 20 test rows in a wide all-lines schema | reference quotes for the premium build; no modelling use |

## 3. Same name, different encoding, granularity or meaning

| Column | Developed | Emerging | Common representation / mapping |
|---|---|---|---|
| age (`driver_age`, `policyholder_age` ↔ `*_age_band`) | integer 17–91 | 5 bands | band the developed age: ≤24 → 17-24, 25–34, 35–49, 50–64, ≥65 → 65+. Any Part 1 age curve must be re-expressed as 5 band relativities. |
| `construction_type` | 11 spellings: Brick/brick/BRICK (70%), non_standard/NON_STANDARD (10%), stone/STONE (8%), W/w (6.3%), T/t (5.8%) | BRK 70%, MIX 10%, STN 8%, WOD 12% | {brick, non_standard, stone, wood}: Brick/brick/BRICK → BRK; non_standard → MIX; stone/STONE → STN; W/w and T/t (wood, timber) → WOD. Shares match to within 0.3 points per class, which supports the mapping. |
| `region` | R01–R12 (12 regions) | E01–E06 (6 regions) | **no mapping** — different geographies. Region is market-specific; any borrowed model must drop it or treat it as a market-local factor re-estimated on emerging data. |
| `occupation` | 20 clean Title-case values + null | 81 spellings (case, trailing space, uniform "Self-employed " prefix) | normalise emerging to the developed list (trim, case-fold, strip prefix, Title case) — done in cleaning (F-15). |
| `customer_since_year` | 2006–2025 | 2008–2025 | both are join-year stamps; common form is tenure = policy year − customer_since_year, which equals `renewal_count` in both markets. Use `renewal_count`. |
| `campaign_code` | null for joiners before 2021 | null for joiners before 2023 | nullness = "joined before the extract window" in both; exclude. |
| `vehicle_age` | 0–28, median 7 | 3–27, median 10, no value < 3 | same unit (years) but a floor of 3 in the emerging market (F-24, team query: definition or market feature?). Keep as is for the emerging model; do not borrow a Part 1 relativity for ages < 3. |
| `elevation_m` | 0–197 | 0–60 | same unit; emerging range is a subset (flatter country). |
| nulls in attribute columns | 2.5% | 12% | same "unknown" level; the rate difference is a data-capture difference, not risk. |
| `exposure` | (days+1)/365 with day-count and 360-day defects | same convention and same defects | recompute from dates in both markets (Part 1 rule R-0001). |
| `sum_insured` | ×1,000 cluster present | ×1,000 cluster present | same per-row ratio rule (R-0013); repaired in cleaning. |
| `channel` | same 3 codes | same 3 codes | identical codes; very different mix (broker 25% vs 70%) — mix, not mapping. |
| `make_model` | 300 codes | same 300 codes (100% overlap) | identical code list; thin per code in the emerging market (≈160 rows each) — use `vehicle_value_group`/`body_type`/`engine_size_cc` as the shared representation and treat make_model as optional. |
| `fuel_type` | electric 8% | electric 2% | same codes; electric is thin in the emerging market. |
| `written_premium` | annual premium | annual premium (not pro-rated for part-year rows) | same meaning; excluded as a feature in both (circular for pricing). |
| `row_id`, `policy_id`, `customer_id`, `address_id`, `claim_id` | 8-digit codes | same formats | **values collide across markets** — never join developed to emerging on any id. |

## 4. Claims table

Identical schema, perils, status codes and valuation date in both markets. Differences are in
levels, not in encoding: bodily-injury mean cost 10.5k vs 21.6k (developed), own-damage 1.1k vs 1.8k,
fire frequency 2.4× developed (see shift_report.md §4). Repudiated claims carry zero amounts in both.

## 5. Weather table

Same seven indices and units; the emerging market's distributions are far outside the developed
range (hail days 14 vs 6, wildfire index 0.53 vs 0.16, freezing days 22 vs 38). Any borrowed
weather relativity would be an extrapolation; weather is excluded from the baseline anyway (F-22).

## 6. Proposed common feature list for a joint or borrowed model

Policy: `*_age_band`, `years_licensed`, `ncb_years`, `vehicle_value_group`, `vehicle_age` (≥3 only),
`engine_size_cc`, `body_type`, `transmission`, `seats`, `fuel_type`, `driver_assist`, `cover_type`,
`overnight_parking`, `vehicle_use`, `named_young_driver`, `voluntary_excess`, `payment_method`,
`new_business`, `renewal_count`, `discount_applied`; `sum_insured`, `construction_type` (mapped),
`occupancy`, `days_unoccupied`, `smoke_alarms`, `accidental_damage_cover`, `mortgage`, `tenure`,
`security_level`, `high_value_items`, `works_from_home`, `lodgers`, `bicycle_cover`.
Customer: `occupation` (normalised), `marital_status`, `household_size`, `prior_claims_5y`,
`licence_points`, `years_at_address`. Address: `urban_density`, `flood_zone`, `distance_to_river_km`,
`elevation_m`, `soil_type`, `building_age`, `property_type`, `roof_type`, `basement`,
`trees_within_5m`, `listed_building`, `bedrooms`, `energy_rating`, `solar_panels`.
Excluded from the common list: `region` (not mappable), `gender` (emerging only), `annual_mileage`,
telematics, `credit_band`, `date_of_birth` (developed only), weather (climate not comparable),
all time stamps and leakage columns.
