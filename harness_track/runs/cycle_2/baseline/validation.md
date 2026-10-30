# Baseline validation — emerging market

Code `work/p40_baseline.py` (one code path for the submission, the second candidate and the holdout file); numbers in
`validation_results.json`; segment tables in `segment_ae.csv`. Model: LightGBM Tweedie (power 1.5), 3 leaves, learning
rate 0.02, extra_trees, min_data_in_leaf 100, feature_fraction 0.8, bagging 0.8, L2 1.0, 6 threads, seeds 11/22/33;
offset log(exposure × completion) + intercept in the init score; target = capped `y_capped`, prediction × line cap
multiplier (1.078 / 1.119 / 1.053); one model per line. Scoring: Tweedie D² (power 1.5) from `tools/tweedie.py`.

## 1. Validation design and where the playbook rules could not be applied as written (R-0206)

| Rule | As written | Why it does not fit | Substitute used | Evidence now weaker |
|---|---|---|---|---|
| R-0201 time-ordered folds | train ≤ Y−1, predict Y, several folds | two training years: exactly one fold | **Primary**: train 2023 → predict 2024 on the observed basis, i.e. ultimate × completion × cap multiplier, scored against observed `y` (the same basis as `holdout_2024.csv`). **Secondary** (labelled weaker): policy-grouped 5-fold on 2023+2024 rows | the secondary fold shares calendar effects between train and test and cannot see level drift; the primary trains on a survivor-only year (F-SURVIVOR-2023) |
| R-0202 adoption on every fold beyond the noise floor (+0.0003) | several time folds | one time fold; seed sd here is 0.0005–0.0064, far above Part 1's floor | adopt only if primary gain > max(0.0003, seed sd of the reference) **and** secondary gain > 0 | effects below ~0.002–0.006 D² are undetectable; adoption rests mainly on one fold |
| R-0203 ≥ 3 seeds | | | 3 seeds on the primary (seed-averaged predictions), 2 on the secondary (5 fits each) | secondary noise not fully characterised |
| R-0207 fix the candidate set before looking | | the first round grid {300, 600, 1200} won at its lower edge on every line | pre-registered edge rule: halve the smallest grid point (floor 50) while it keeps winning; feature groups then tested at the chosen round count | the grid extension was registered after the first result, as a rule, not as a point |
| R-0312 re-choose capacity on a grid | half / default / double | | grid extended to {50 … 1200} by the edge rule | — |
| R-0307 segment corrections only when every fold agrees | | one fold | A/E tabulated on the fold for pre-registered segments (new_business, channel, age band, payment_method, mid-term rows); **no correction adopted** | the new-business relativity for the property lines is unresolved (section 5) |
| R-0208 level vs history | | — | done below, raw and completion-adjusted, on cleaned and as-delivered tables (R-0507) | — |
| R-0204 public-leaderboard noise | | the agent does not submit | not applicable; for the human: the public set here is a third of ≈209k rows, about 1.7× noisier than Part 1's ≈0.0009 pairwise, i.e. ≈0.0015 | — |
| R-0305 blend; R-0306 credibility | | one family only in the baseline; 76% of the test book has no history | not built / not tested (see adaptation_decisions.md) | — |

Pre-registered candidate set: round grid (above); feature groups added one at a time to the lean set: weather (7
columns), marketing (email_domain, marketing_consent, document_preference, previous_insurer, branch_id,
marketing_segment), premium (written_premium), behaviour (missed_payments_12m, days_quote_to_inception), gender
(information only, never adopted automatically). Lean set per line: `validation_results.json → lines → lean_features`.

## 2. Scores on the primary fold (2023 → 2024, observed basis) and the secondary fold

Tweedie D², mean of seeds (± sd across seeds) for the primary fold; "NB" = the new-business subset of 2024 (R-0406);
"level" = Σ prediction / Σ observed on 2024 rows.

| Line | Config | Primary D² | NB subset | Level | Secondary D² |
|---|---|---|---|---|---|
| motor | 2023 level only (no features) | 0.0499 | — | 0.958 | — |
| motor | lean, 1200 rounds | 0.0287 ± 0.0009 | 0.078 | 0.932 | 0.0200 |
| motor | lean, 600 (Part 1 default) | 0.0400 ± 0.0019 | 0.089 | 0.935 | 0.0279 |
| motor | lean, 300 | 0.0535 ± 0.0013 | 0.098 | 0.937 | 0.0395 |
| motor | lean, 150 | 0.0610 ± 0.0019 | 0.100 | 0.939 | 0.0460 |
| motor | **lean, 75** | **0.0633 ± 0.0005** | 0.098 | 0.943 | 0.0453 |
| motor | lean, 50 | 0.0623 ± 0.0008 | 0.096 | 0.946 | 0.0428 |
| motor | lean + weather, 75 | 0.0628 ± 0.0011 | 0.097 | 0.943 | 0.0446 |
| motor | lean + marketing, 75 | 0.0639 ± 0.0010 | 0.096 | 0.947 | 0.0457 |
| motor | lean + premium, 75 | 0.0645 ± 0.0010 | 0.097 | 0.947 | 0.0473 |
| motor | lean + behaviour, 75 | 0.0626 ± 0.0000 | 0.097 | 0.942 | 0.0447 |
| motor | lean + gender, 75 (information) | 0.0632 ± 0.0010 | 0.097 | 0.944 | 0.0460 |
| motor | **chosen: lean + marketing + premium, 75, seed-averaged** | **0.0658** | 0.0965 (renewal 0.057) | 0.949 | — |
| buildings | 2023 level only | −0.0195 | — | 1.586 | — |
| buildings | lean, 1200 | 0.0185 ± 0.0047 | −0.047 | 1.588 | 0.0230 |
| buildings | lean, 600 | 0.0308 ± 0.0025 | −0.011 | 1.572 | 0.0439 |
| buildings | **lean, 300** | **0.0343 ± 0.0039** | 0.018 | 1.559 | 0.0589 |
| buildings | lean, 150 | 0.0274 ± 0.0014 | 0.034 | 1.549 | 0.0608 |
| buildings | lean + weather, 300 | 0.0307 ± 0.0018 | 0.018 | 1.561 | 0.0574 |
| buildings | lean + marketing, 300 | 0.0080 ± 0.0021 | −0.059 | 1.547 | 0.0363 |
| buildings | lean + premium, 300 | 0.0345 ± 0.0035 | 0.011 | 1.582 | 0.0613 |
| buildings | lean + behaviour, 300 | 0.0350 ± 0.0036 | 0.020 | 1.561 | 0.0601 |
| buildings | lean + gender, 300 (information) | 0.0327 ± 0.0057 | 0.020 | 1.560 | 0.0595 |
| buildings | **chosen: lean, 300, seed-averaged** | **0.0347** | 0.018 (renewal 0.025) | 1.560 | — |
| contents | 2023 level only | 0.0455 | — | 1.021 | — |
| contents | lean, 1200 | −0.0018 ± 0.0030 | −0.061 | 1.037 | 0.0618 |
| contents | lean, 600 | 0.0239 ± 0.0064 | 0.012 | 1.040 | 0.0743 |
| contents | **lean, 300** | **0.0504 ± 0.0042** | 0.070 | 1.040 | 0.0763 |
| contents | lean, 150 | 0.0621 ± 0.0028 | 0.103 | 1.037 | 0.0717 |
| contents | lean, 75 | 0.0630 ± 0.0003 | 0.119 | 1.035 | 0.0621 |
| contents | lean, 50 | 0.0598 ± 0.0016 | 0.122 | 1.034 | 0.0569 |
| contents | lean + weather, 300 | 0.0491 ± 0.0020 | 0.068 | 1.043 | 0.0757 |
| contents | lean + marketing, 300 | 0.0323 ± 0.0054 | 0.095 | 1.042 | 0.0640 |
| contents | lean + premium, 300 | 0.0492 ± 0.0043 | 0.069 | 1.065 | 0.0779 |
| contents | lean + behaviour, 300 | 0.0502 ± 0.0034 | 0.069 | 1.040 | 0.0745 |
| contents | lean + gender, 300 (information) | 0.0517 ± 0.0030 | 0.075 | 1.040 | 0.0777 |
| contents | **chosen: lean, 300, seed-averaged** | **0.0509** | 0.071 (renewal 0.047) | 1.040 | — |

Reading:
- **Capacity**: Part 1's 600 rounds over-fit every line; 1200 is worse than a level-only model on two lines. Motor
  settles at 75 rounds (both folds agree; 50 is slightly worse). Contents prefers 75–150 on the primary fold but the
  secondary fold falls monotonically below 300, so the rule stops at 300 (the two folds disagree on where between 75
  and 300 the optimum sits; the primary difference 0.0126 is twice the seed sd). Buildings: 300 on the primary, 150
  marginally better on the secondary; 300 passes, 150 does not.
- **Feature groups**: weather never passes (as in Part 1). Marketing is destructive on both property lines (−0.026
  and −0.018 primary) and marginally positive on motor (+0.0007 primary, above the 0.0005 floor; +0.0003 secondary),
  adopted by the rule for motor only. Own premium passes for motor (+0.0013 / +0.0020) and fails for the property
  lines. Behaviour never passes. Gender would add +0.0013 on contents and nothing on motor or buildings; not adopted
  (team decision). The adopted motor groups are small gains of the order of the floor; the lean-only motor model
  (0.0633) is a defensible alternative for a team that prefers Part 1's lean principle.
- **New-business subset**: D² on 2024 new business is higher than overall for motor and contents (more signal in a
  higher-frequency segment) and negative for buildings at high round counts.
- **Level on the fold**: motor 0.95 (2024's completed cost is 4.4% above 2023's and the model carries the 2023
  level); buildings 1.56 (the 2023 training year carries nine fire losses above 100k, see target_notes.md §5–7);
  contents 1.04. The mix diagnostic shows the 2023 model predicts the same ultimate rate on 2024 rows as on 2023 rows
  (motor 440 vs 442; buildings 507 vs 501; contents 93 vs 92), so the fold level gaps are period effects, not mix.

## 3. Capacity, grid and adoption (R-0312, R-0207)

Grid tested: motor {50, 75, 150, 300, 600, 1200} → 75; buildings {150, 300, 600, 1200} → 300; contents
{50, 75, 150, 300, 600, 1200} → 300. Adoption table (gain primary, gain secondary, floor, adopted) in
`validation_results.json → lines → adoption`. Chosen feature counts: motor 37, buildings 34, contents 35.

## 4. Level check on the training rows (R-0311) and the level factor

The R-0311 check **failed** in the first run: with the intercept in the init score, Σ prediction / Σ target on the
training rows was 0.95 (motor), 0.83 (buildings), 0.87 (contents). Shallow, regularised Tweedie boosting with
bagging and few rounds does not preserve the total on data this small. The pipeline therefore applies one
multiplicative level factor per fit (training total ÷ fitted total) and reports it: the factor is 1.03–1.09 on motor
fits, 1.03–1.57 across all buildings and contents fits (largest at 1,200 rounds and on the small policy-grouped
folds). After the factor Σ prediction = Σ target on training rows to 4 decimals for every line (`train_level_check`).
The holdout and submission files are produced with the factor.

## 5. Level against history (R-0208, R-0507) and segment actual / expected (R-0307, R-0309, R-0410)

Predicted CU per exposure-year on the 2025 test rows (ultimate, completion = 1), candidate A (flat) and B (developed
trend for two years: ×1.043 / ×1.126 / ×1.108):

| Line | Test exposure | A | A new business | A renewals | B | History raw at valuation 2023 / 2024 | History completed 2023 / 2024 | Two-year completed | Max prediction A |
|---|---|---|---|---|---|---|---|---|---|
| motor | 79,007 | **477.3** | 484.7 | 452.7 | 497.8 | 432.7 / 382.7 | 443.2 / 462.8 | 453 | 873 |
| buildings | 47,376 | **423.4** | 423.5 | 422.8 | 476.6 | 514.3 / 306.7 | 515.8 / 325.4 | 417 | 5,797 |
| contents | 59,017 | **94.2** | 95.1 | 91.2 | 104.5 | 91.1 / 86.8 | 91.4 / 89.5 | 90 | 589 |

One sentence per line (candidate A): **motor** sits 5% above the two-year completed level because the test book is
younger and 77% new business, both priced above average; **buildings** reproduces the two-year completed level (the
model cannot know whether 2023's fires or 2024's calm is the norm; A/E on the fold was 1.56 for that reason);
**contents** sits 4% above the two-year level for the same mix reason as motor, with a smaller new-business
relativity. Candidate B adds the borrowed trend on top (4 / 13 / 11%).

`tools/check_sub.py` printouts (R-0507): against the **cleaned** tables the raw history is motor 432.7 / 382.7,
buildings 514.3 / 306.7, contents 91.1 / 86.8 CU per exposure-year (2023 / 2024). Against the **as-delivered** tables
the same history reads 20–40% lower (motor 307.7 / 275.8, buildings 312.0 / 246.7, contents 70.0 / 63.2), because
the 114 day-count rows inflate stored exposure by 15,461 / 10,315 / 9,835 exposure-years (profile.md §9): the exposure
repair alone moves the history level by a quarter to a third, and a model levelled on the as-delivered history would be
that much too cheap. The two printouts:

```
# python tools/check_sub.py outputs/baseline/submission.csv          (as-delivered history)
motor     test rows  90,521 | predicted CU per exposure-year    477.3 | history (raw, at valuation) 2023: 307.7, 2024: 275.8 | max prediction 873
buildings test rows  52,295 | predicted CU per exposure-year    423.4 | history (raw, at valuation) 2023: 312.0, 2024: 246.7 | max prediction 5,797
contents  test rows  66,247 | predicted CU per exposure-year     94.2 | history (raw, at valuation) 2023: 70.0, 2024: 63.2 | max prediction 589
# python tools/check_sub.py outputs/baseline/submission.csv --cleaned  (cleaned history)
motor     test rows  90,521 | predicted CU per exposure-year    477.3 | history (raw, at valuation) 2023: 432.7, 2024: 382.7 | max prediction 873
buildings test rows  52,295 | predicted CU per exposure-year    423.4 | history (raw, at valuation) 2023: 514.3, 2024: 306.7 | max prediction 5,797
contents  test rows  66,247 | predicted CU per exposure-year     94.2 | history (raw, at valuation) 2023: 91.1, 2024: 86.8 | max prediction 589
```
Candidate B on cleaned history: 497.8 / 476.6 / 104.5 (max predictions 910 / 6,527 / 653). Both files pass the hard
checks (row count, unique ids, no nulls, non-negative).

**Actual / expected on the 2024 fold** (chosen models trained on 2023; from `segment_ae.csv`):

| Segment | motor | buildings | contents |
|---|---|---|---|
| overall | 1.05 | 0.64 | 0.96 |
| new business / renewal | 1.21 / 1.04 | 0.49 / 0.66 | 1.43 / 0.92 |
| channel broker / direct / comparison | 1.04 / 1.09 / 1.12 | 0.69 / 0.47 / 0.85 | 1.00 / 0.88 / 0.83 |
| age 17-24 / 25-34 / 35-49 / 50-64 / 65+ | 1.13 / 1.26 / 0.73 / 0.82 / 1.12 | 0.45 / 0.36 / 0.72 / 0.93 / 0.80 | 1.30 / 1.01 / 0.59 / 1.00 / 0.87 |
| rows after a mid-term change (second row) / first row of the pair | 1.15 / 1.01 | 0.20 / 1.02 | 1.92 / 0.36 |

- **New business (R-0410)**: the model prices new business almost flat. Its implied new-business relativity on the
  test book is motor ×1.07, buildings ×1.00, contents ×1.04 (not age-standardised), against pre-model
  age-standardised cost ratios of ×1.45, ×0.85 and ×1.28 (shift_report.md §5). On the fold, new-business rows are
  under-predicted relative to renewals by 16% (motor) and 55% (contents), consistent with that gap; buildings new
  business (77 claims) is over-predicted along with everything else in the fire-year fold. This is the R-0410 warning
  realised: with 8% of training exposure the trees do not learn the segment. No correction is applied (one fold,
  R-0307); the candidate correction is a new-business multiplier shrunk toward 1, e.g. ×1.2 motor and ×1.2 contents,
  which would raise the test level by about 15% in both lines. Listed as an open decision.
- **Age bands**: 35-49 and 50-64 over-predicted and 25-34 under-predicted on the fold in motor; the same middle-age
  over-prediction in contents. One fold, 4–5k rows per band; noted, not corrected.
- **Mid-term change (R-0309)**: Part 1 over-predicted rows after a mid-term change by 11–15%; here motor second rows
  are *under*-predicted by 15% and the property lines swing wildly on 500–1,000 rows. The Part 1 correction does not
  carry over; no correction applied.
- **Channel**: broker, the 70% channel, is predicted within 4% on motor and contents; direct and comparison-site are
  thin.

## 6. Deviance decomposition (R-0107) and feature importance

Share of total deviance on the 2024 fold: zero-claim rows 60% / 67% / 55% (motor / buildings / contents), ordinary
claim rows 32% / 25% / 40%, top-1% claim rows 8% / 9% / 5%. Frequency discrimination dominates as in Part 1; severity
refinements can move at most the last 5–9%. Top gain features: motor make_model, written_premium, marketing_segment,
ncb_years, driver_age_band; buildings occupation, flood_zone, energy_rating, construction_type, year_built; contents
occupation, flood_zone, sum_insured, elevation_m, urban_density. The weight on `make_model` (300 levels, 20k rows) and
on `occupation` in the property lines is a plausible over-fit of high-cardinality categoricals and the first thing a
GLM member would regularise differently.

## 7. Holdout file (`holdout_2024.csv`)

Every 2024 training row of the three lines (25,603 + 14,867 + 18,732 = 59,202 rows), predicted by the chosen
configuration trained on **2023 rows only** (no 2024 emerging row, no developed data), on the observed basis
ultimate × completion × cap multiplier, candidate A (no trend). Scores against observed `y`: D² motor 0.0658, buildings
0.0347, contents 0.0509; Σ prediction / Σ observed 0.95 / 1.56 / 1.04. `holdout_2024_B_devtrend.csv` applies one year
of the developed trend (D² 0.0661 / 0.0278 / 0.0511; levels 0.97 / 1.65 / 1.09). The file is produced by the same
`fit_predict` code path as the submission; read its buildings level as the fire-year effect, not as a model defect.

## 8. Files

- `submission.csv` — candidate A (flat trend), 209,063 rows, passes `check_sub.py` on cleaned and as-delivered history.
- `submission_B_devtrend.csv` — candidate B (developed trend, two years). Only one can be selected (R-0505); the human
  records the choice and why.
- `holdout_2024.csv`, `holdout_2024_B_devtrend.csv` — see §7.
- `validation_results.json`, `segment_ae.csv` — all numbers above.

## 9. What is weaker than in Part 1, ranked by effect on the predicted level

1. The new-business relativity (flat in the model vs +28–45% pre-model cost excess in two lines): up to 15% of level.
2. Trend (A vs B): 4–13% of level; no local evidence.
3. The 2023 survivor sample and the 2023 vs 2024 level difference (motor +4%, buildings −37%, contents −2%
   completed): the two-year average is used; the direction of the truth is unknown.
4. Completion tail borrowed from the developed market: ±3% on motor 2024, ±1.5% on the two-year level.
5. Cap multiplier on buildings: ±3%.
6. Capacity and feature-group choices: a few thousandths of D², no level effect.
