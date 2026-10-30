# Answer key — emerging market profile (architect-side, 2026-10-24)

Produced by the architect BEFORE Cycle 1, independently of the harness.
Never shown to the agent. Items marked NEW were not in the Week 1 README.

## Sizes and shape
- Train rows: motor 47,283 · buildings 27,447 · contents 34,566 (2023–24).
  Claims 9,258 (motor 7,183 · buildings 1,059 · contents 1,016; BI only 450).
- Test rows: motor 90,521 · buildings 52,295 · contents 66,247 (≈3× one
  train year). new_business 76%; broker ≈70% (train ≈70% too);
  renewal_count mean 6.9 → 1.8; ncb_years 6.4 → 6.0 (carried from prior
  insurer); age 17–34 share 39% → 50%; 65+ share 28% → 24%.
- customer_since_year = 2025 for 63,810 of test-motor customers.
- Weather table has 2023, 2024 AND 2025 (data page says 2023–24).
- Regions E01–E06; E03 = 29% of addresses. Construction BRK/WOD/MIX/STN.
- Report lag: p50 8 d, p90 37 d, p99 317 d. Loss dates to 2024-12-29.

## Data-quality items
| # | Item | Scale | Week 1 rule fires? |
|---|---|---|---|
| 1 | exposure stored in days (365, 186) | motor 47 / bldg 33 / cont 34 rows; test 0 | yes (R-0001) |
| 2 | sum_insured ×1000 | bldg 53 train / 104 test; cont 57 / 135 | yes (R-0003); test rows matter |
| 3 | claims with loss_date outside any policy period for that policy (34 of them dated 2021–22, before the market existed) | 36 claims | NEW (R-0004 should surface the unmatched share) |
| 4 | duplicate claims differing only by claim_id | 0 | R-0002 checks; should log "none found" |
| 5 | customer_service_contacts: train mean 0.81, test 0.40; p99 6 vs 2 | all rows | yes (R-0005) |
| 6 | customer_since_year separates train from test | 70% of test customers | yes (R-0006) |
| 7 | occupation free text: "Retired"/"retired"/"Retired ", "Self-employed X" prefix, 81 variants, 16,517 null (12%) | customers | NEW |
| 8 | block-missing customer fields: occupation, marital_status, household_size, years_at_address ≈16k each | customers | NEW — check link to channel / new business |
| 9 | motor nulls vehicle_age 5,604 / engine_size_cc 5,745 / overnight_parking 5,697 (train); ≈11k each (test) | ≈12% | note |
| 10 | expenses: commission_comparison_site blank for emerging; test has comparison_site channel (motor 4,530 / bldg 2,624 / cont 3,304 rows) | — | report judgment flag |
| — | no negative paid, no incurred<paid, no recoveries>incurred, no report_date<loss_date | — | clean |

## Burning cost (net incurred excl. repudiated / exposure-year), raw, no IBNR
| line | 2023 | 2024 |
|---|---|---|
| motor | 307.7 (freq 0.134) | 275.8 (freq 0.125) |
| buildings | 312.0 (0.028) | 246.7 (0.036) |
| contents | 70.0 (0.027) | 63.2 (0.025) |
Open share 2024: motor 20%, buildings 25%, contents 12% (2023: 4%, 4%, 0%).

## Peril mix (claims, avg incurred)
motor: own_damage 2,712 (1.4k), third_party_prop 2,263 (2.4k), glass_hail
1,350 (0.8k), bodily_injury 450 (10.7k), theft 408 (4.1k).
buildings: storm 466 (2.6k), escape_of_water 268 (3.9k), accidental_damage
122 (0.9k), flood 81 (26k), fire 70 (62k), subsidence 52 (14k).
contents: theft 418 (2.9k), accidental_damage 340 (0.6k), escape_of_water
172 (2.1k), flood 86 (9.2k).

## Expenses (emerging vs developed)
fixed 85 vs 45 CU; variable 15% vs 12%; commission broker 20% vs 15%,
direct 0, comparison_site blank vs 10%; premium tax 8% vs 12%; cat
reinsurance 12% vs 6% of property risk premium; profit 8% vs 5%.

## Corrections after cycle 1 (2026-10-26)
- Burning-cost table above used the RAW exposure column, which carries the day-count rows; on repaired exposure the raw-at-valuation rates are motor 432.7 / 382.7, buildings 514.3 / 306.7, contents 91.1 / 86.8 (2023 / 2024). The grader now derives exposure from dates.
- Item 1 missed a second exposure convention: 493 rows on a 360-day basis (+1.39%); the key's |Δ| > 0.02 tolerance hid it. Found by the agent (F-02).
- Item 8 ("block-missing, broker feed") was a guess; the agent's MCAR evidence (independent ~12% draws across 15 columns, no link to channel or year) is better supported.
- Not in the key, verified after the run: campaign_code null ⇔ joined before 2023 (perfect cohort stamp); ncb_years > years_licensed on 16.4% / 22.2% of motor rows; 2024 full-year rows end 30 Dec; 10.0% of DEVELOPED motor rows reference customers absent from developed customers.parquet (Part 1 issue).
