# Adaptation decisions — what carries over from Part 1

One row per component. "Carry over" is one of: AS-IS (used unchanged), ADAPTED (method kept,
parameters or inputs changed), RE-ESTIMATED (method kept, values re-fitted on emerging data),
BORROWED (taken from the developed market because emerging data cannot support it), DROPPED.
Evidence names the file or table that supports the decision. Remaining uncertainty says what could
still be wrong and, where known, how much the predicted level moves if it is (sensitivity).

| Component | Part 1 choice | Carry over | Evidence | Remaining uncertainty / sensitivity |
|---|---|---|---|---|
| Data-quality treatments (exposure, unit scale, duplicates, linkage) | Recompute exposure from dates; rescale ×1,000 sums insured by proportionality ratio; dedupe exact copies; link claims by loss date | **AS-IS** — the same four defects exist here (114 day-count rows, 495 on a 360-day basis, 349 ×1,000 sums insured incl. 239 test rows, 36 unlinkable claims); duplicates: none | findings.json F-01…F-08; profile.md §7; work/cleaning_log.json | Low. The 36 excluded claims are 0.33% of cost (motor 0.4%) — the level moves by that if the team rules them genuine late reports. The ×1,000 boundary (log-ratio 4.0) sits in an interval empty on every table. |
| Leakage exclusions (in-period behaviour counts, join-year identifiers) | Exclude customer_service_contacts, campaign_code, customer_since_year; keep tenure forms | **AS-IS** plus one addition: weather excluded as a calendar stamp (2025 values differ for every address) and row shape (start month, row length) excluded | shift_report.md §2, §6; work/adversarial_single_auc.csv | Weather exclusion is a judgment: 2025 weather is known at pricing time, but a model trained on 2023–24 weather would extrapolate. Re-adding it is a registered group test (R-0302). |
| Target definition (net incurred, repudiated = 0) | y = Σ(incurred − recoveries), repudiated 0, linked by loss date | **AS-IS**; reconciles to the cent (27,997,991.57) | target_notes.md §1 | None on definition. 120 repudiated claims carry 0 amounts here. |
| Completion / IBNR curve (source years, tail) | Cost-weighted lag curve from mature years; offset log(exposure × completion) | **ADAPTED + BORROWED tail**: truncation-corrected product-limit curve on 2023–24 claims (observed to 540 days), developed curve beyond 540 days; capped at 50k; no-tail and count variants carried | target_notes.md §3; work/completion_summary.json; work/lag_curves.parquet | Borrowed share 2.3% of motor ultimate (≈0 property). If the emerging BI tail is twice the developed one, 2024 motor ultimate +2.9%. R-0109 check agrees within 0.5 pts. 2024 motor completion 0.80: a ±0.02 error is ±2.5% of the 2024 level. |
| Trend (fit years, extrapolation to 2025) | Log-linear on mature years | **BORROWED**: cannot be fitted on two years; developed 2021–23 capped, completion-adjusted trend: motor ≈0% (floored), buildings +6%, contents +5%; 1.5 years to the test midpoint; two candidate files | target_notes.md §4; work/ibner_trend_summary.json | Full range: motor −2% to +4%/yr → ±5% on level; buildings 0–8% → 0 to +12%; contents 0–7% → 0 to +11%. The emerging 2024/2023 ratios (+7%, −27%, −2%) are not trend. |
| Large-loss cap and redistribution | Cap at top 1% of positive targets, redistribute as a line multiplier | **RE-ESTIMATED** on emerging rows: caps 21,148 / 143,434 / 19,968; multipliers 1.078 / 1.119 / 1.053 | target_notes.md §5; work/modelling_tables_summary.json | Buildings multiplier rests on 10 rows (one 361k fire = 9.7% of 2024); ±0.05 on the multiplier is ±5% of the buildings level. |
| IBNER view on open claims | Compare open vs closed; do not adopt blind | **AS-IS (not adopted)**; compared against the developed market at the same valuation (same open shares, no under-reserving signal in the mature developed year) | target_notes.md §6 | 2024 open claims are 38% / 35% / 18% of line cost; ±10% on their settlement = ±3.8% / ±3.5% / ±1.8% on the 2024 level. Not testable locally. |
| Feature set (lean vs full; new/missing columns) | Lean (no weather, channel, marketing, calendar) beat full and top-K | **ADAPTED**: lean set re-chosen for this schema (age bands instead of age; gender added; make_model dropped as too thin; no mileage/telematics/credit band). Lean beat full on the 2023→2024 fold in all three lines (D² 0.077 vs 0.057, 0.043 vs 0.027, 0.058 vs 0.051) | baseline/validation.md; work/baseline_results.json | Single fold. Gender as a rating factor needs a regulatory check (team query). make_model could be re-added as a target-encoded or grouped variable. |
| Schema mapping (age bands, construction codes, free text) | Integer age, free-text construction, clean occupation | **ADAPTED**: developed age banded to the 5 emerging bands; construction free text → BRK/WOD/STN/MIX; occupation noise normalised to the developed list; region not mappable | schema_mapping.md | Any Part 1 age relativity finer than 5 bands is lost. Region relativities cannot be borrowed at all. vehicle_age floor of 3 (definition?) is a team query. |
| Model family and complexity (tree depth, regularisation) | LightGBM Tweedie 1.5, 3 leaves, lr 0.02, ≈600 rounds, extra_trees | **ADAPTED**: same family and shape; rounds re-chosen per line on a pre-registered grid {150, 300, 600} with edge rule and 100-round floor → motor 600, buildings 300, contents 300 (primary fold preferred 100 but the policy-grouped check preferred 300, so the smaller count was not adopted); leaf-step guard (max_delta_step 0.7) added after the first run lost 7–40% of level with rounds | baseline/validation.md | Capacity is chosen on one time fold + one weaker grouped fold; property choices move by ±0.002 D² with seed. |
| Offset / weighting scheme | Offset log(exposure × completion), init score at the training level | **AS-IS**, with the R-0311 gate enforced: Σpred/Σy on training rows was 0.97 / 0.87 / 0.89 after fitting and explicit level factors (1.03 / 1.15 / 1.13) were applied and reported | baseline/validation.md | The size of the property factors says the learner under-fits the level on 1k claims; a GLM intercept refit or fewer regularisers would remove the need. Level is restored exactly on training rows either way. |
| Blend composition and weights | Equal-weight blend of shallow GBMs, GLM, additive, NN; seed-averaged | **DROPPED for the baseline** (single family, 3 seeds); recommendation: at most 2–3 regularised members if any | validation.md | A blend cannot be validated on one fold beyond the noise floor (seed sd 0.0003–0.002 here vs Part 1 0.001). |
| Policy-level claim-count credibility | (k + N)/(k + L), k ≈ 12, renormalised | **DROPPED**: 76% of test rows have no history (identity), and the 24% renewals have at most 2 years; expected gain too small to validate | shift_report.md §2, §5 | Could be revisited for the renewal book once a second renewal year exists. |
| Line-level level (base rate) | From developed data | **RE-ESTIMATED** on emerging data (ultimate burning cost 2023/2024: motor 447/478, buildings 515/325, contents 91/89) — developed levels do not transfer (motor 74% of developed, contents 78%, buildings ≈100% capped) | shift_report.md §4; target_notes.md §7 | Buildings is the least credible: the two years differ by 37% on 28 fire claims; the baseline sits at 428 (no trend) / 468 (trend). Motor test level 577 is 21% above the 2024 ultimate because the acquired book is 76% new business with a fitted relativity of 1.48 (pre-model 1.43). |
| Segment-level corrections | Actual/predicted by segment on every fold; correct only if consistent on all folds, shrunk | **AS-IS as a procedure, no correction applied**: only one time fold exists; 2024 actual/predicted by new_business, age band, channel, payment method, region is reported | validation.md | Candidates seen once: motor renewals under-predicted (a/p 1.12) and new business over-predicted (0.89) by the 2023-only model; contents new business under-predicted (a/p 1.43, model relativity ≈1.0 vs pre-model 1.23–1.29). Each is a ±10–17% line-level question that one fold cannot settle. |
| Validation design (folds, noise floor, seeds) | Time-ordered folds (3 in Part 1), noise floor +0.0003, ≥3 seeds | **ADAPTED**: one time fold (2023 → 2024, trained on the survivor year), one policy-grouped 3-fold within 2023–24 as a labelled weaker check, 3 seeds, new-business subset scored; developed folds not re-run | validation.md | Evidence for any change is weaker than Part 1's; the primary fold trains on a survivor sample and predicts a 20%-incomplete year through the completion offset. |

## What changed in this market (summary)

The customers are younger (17–34 is 40% of training rows and 50% of the 2025 book, against 29–33%
in the developed market), reach us mainly through brokers (70% vs 25%), have no telematics,
mileage or credit information, and are recorded with age bands only. The climate is hotter, wetter,
hail- and wildfire-prone with few frosts: buildings fire frequency is 2.4× the developed market and
escape-of-water half of it, motor glass/hail frequency is 46% higher. Cost levels are lower across
every motor peril (bodily injury 10.5k vs 21.6k, own damage 1.1k vs 1.8k) while motor frequency is
35% higher — a compensation/repair-cost regime, not a mix effect. The 2025 book is 76% new business
transferred from a broker, absent from training, with the same age and channel profile as the small
training new-business segment, which runs 18% / 40% above renewals in motor frequency / cost.
The expense base differs too (fixed expense 85 vs 45 CU, broker commission 20% vs 15%, premium tax
8% vs 12%, cat reinsurance 12% vs 6%; comparison-site commission not supplied).

## Borrowed assumptions — list and sensitivity

| Borrowed item | Why | Effect on predicted level if wrong by a plausible margin |
|---|---|---|
| Report-lag tail beyond 540 days (developed product-limit curve, complete at 1,400 days) | emerging claims observed to 730 days at most, thin beyond 540 | motor 2024 completion 0.804; tail twice as heavy → 0.78 → **+2.9% motor**; property ≈ 0 |
| Trend to mid-2025: motor 0%, buildings +6%/yr, contents +5%/yr (developed 2021–23, capped, completion-adjusted) | two accident years, one incomplete | motor −2…+4%/yr → **±5%**; buildings 0…8% → **−9%…+3%** around the central +9%; contents 0…7% → **−8%…+3%** around +7.6% |
| Shape of relativities for shared attributes (age bands, vehicle, property) as a prior — used only as a sanity reference, not imposed | 7k / 1k / 1k claims | none on level directly; if used to regularise a future model, the region/weather/mileage parts cannot be borrowed |
| Open-claim adequacy: developed market shows no under-reserving at the same stage → no IBNER uplift | one snapshot locally | ±10% on open claims → **±3.8% motor, ±3.5% buildings, ±1.8% contents** on the 2024 level |
| Part 1 modelling recipe (Tweedie 1.5, 3 leaves, lr 0.02, lean features, equal-seed average) | one local fold only | rounds re-chosen locally; a different capacity moves fold D² by ≤0.01 and the level not at all (level is gated) |
| Noise floor +0.0003 D² and "adopt only if every fold agrees" | cannot be re-measured on one fold | seed sd here 0.0003 (motor) to 0.002 (property): property decisions below 0.004 are noise |

## Open decisions for the team

1. **Motor acquired book**: the baseline prices 2025 new business at 1.48× renewals (pre-model
   age-standardised 1.43; the 2023-only model over-predicted 2024 new business by 12%). If the
   transferred book behaves like renewals, the motor level is 21% too high; if like our new
   business, it is right. This is the largest single level question and cannot be validated locally.
2. **Contents new business**: the model prices it ≈ flat (1.02×) against a pre-model 1.23–1.29× on
   102 claims; applying the pre-model relativity to the 76% new-business test rows raises the
   contents level ≈ 17%. Not applied (one fold); decision needed.
3. **Buildings level**: 2023 (fire year, 515 ultimate) vs 2024 (325); the model averages to 428 and
   the trend candidate adds 9%. Whether 2023's 49 fires are a cat-like event to load separately
   (cat reinsurance is 12% of property risk premium in the expense table) is a pricing decision.
4. **Trend candidate**: submission.csv (borrowed trend) vs submission_no_trend.csv — choose one.
5. **36 excluded claims** (F-08): confirm they are date defects, not genuine late reports.
6. **Gender** as a rating factor (emerging-only column; top-6 gain in the motor model) — regulatory check.
7. **`declined_by_insurer`** semantics (F-18) and **comparison-site commission** (F-17) for the
   premium build; **vehicle_age floor of 3** (F-24) before any vehicle-age relativity is borrowed.
8. Whether to re-add weather (as address-level climate rather than year values), make_model
   (grouped) and written_premium as feature groups — each a registered test against the fold.
