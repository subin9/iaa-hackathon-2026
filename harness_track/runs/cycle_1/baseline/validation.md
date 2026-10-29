# Baseline validation — emerging market 2025

Code: `work/p40_baseline.py` (inputs `outputs/modelling_tables/`, outputs `submission.csv` = candidate A, `submission_zero_trend.csv` = candidate B, `holdout_2024.csv`, statistics `work/baseline_stats.json`, console log `work/p40_out.txt`). Metric: Tweedie D², power 1.5 (`tools/tweedie.py`). Seeds 0, 1, 2; 6 threads; lightgbm 4.7.0.

## 1. Model

One LightGBM Tweedie model per line, Part 1's winning shape (R-0301) with stronger leaf regularisation for 25× less data: power 1.5, 3 leaves, learning rate 0.02, extra_trees, feature_fraction 0.8, bagging 0.8, min_data_in_leaf 200, L2 = 1, categorical smoothing 20. Target `y_capped` (99th-percentile cap, target_notes §5); predictions multiplied by the line's redistribution multiplier (1.0773 / 1.1200 / 1.0482). Init score = log(exposure × completion / trend_factor) + log(mean rate of the training set), so the trees learn relativities and the level reconciles to the training years by construction (Σ prediction on training rows = Σ y_capped). Three seeds averaged. Lean feature set (R-0302): policy risk factors, customer risk factors, address attributes — 43 (motor), 36 (buildings), 37 (contents) columns; no weather, channel/payment, marketing, make_model, colour or gender (listed in `modelling_tables/README.md`; the baseline excludes gender pending the rating-rule decision).

Rounds: Part 1's 600 is the default; 300 and 1,000 were pre-registered alternatives, adopted only if they beat 600 by more than 3 seed-sd on the primary fold and were not worse on the secondary check. Result: motor 300 (+0.0028, 4.7 sd; secondary +0.0010), buildings 600 (neither alternative better), contents 300 (+0.0298, 15 sd; secondary +0.0075). The smaller lines over-fit at Part 1's round count.

## 2. Validation design and where the playbook rules could not be applied as written (R-0206)

- Primary fold (R-0201): train on 2023 rows only, predict every 2024 row on the observed basis (rate × exposure × completion × 1/trend_factor_2024) and score against `y` as reported at 31 Dec 2024. This is the only time-ordered fold the market allows.
- Secondary, weaker check: policy-grouped 5-fold over 2023-2024 together (a policy's rows are in one fold, but its 2023 and 2024 rows are scored by models that saw the other year). Used only as a "does not hurt" check for changes adopted on the primary fold; its D² is not comparable with the primary fold's.
- R-0202 (every fold in the same direction) cannot be applied with one fold. Substitute: primary fold beyond 3 seed-sd and not worse on the secondary. The developed market's folds were not run as a direction check for method changes (time); this weakens every adoption below.
- R-0203 (noise floor): Part 1's ±0.001 was measured on 600k-row folds. Measured here from three seeds on the primary fold: motor 0.0006, buildings 0.0042, contents 0.0020 — property noise is 2-4× Part 1's, so effects below ~0.01 D² in property are not readable on one fold.
- R-0204 (public leaderboard noise): no public score was used or estimated.
- R-0205 / R-0305 (blend): no blend in the baseline; a single family, seed-averaged. Nothing to weight.
- R-0306 (credibility): dropped; 76% of the test rows have no history.
- R-0307 (segment corrections): segments pre-registered (age band, channel, new_business, tenure band, post-mid-term-change rows); reported on the one fold, none applied.
- R-0406: new-business subset scored separately (below).

## 3. Scores

| line | primary fold D², lean/600 (3-seed mean ± sd) | rounds chosen | primary fold D², chosen | secondary grouped D² (chosen / 600) | new-business subset D², A/E (rows, claims) | renewal subset D², A/E | holdout 2024 D² with multiplier | holdout A/E |
|---|---|---|---|---|---|---|---|---|
| motor | 0.0703 ± 0.0006 | 300 | 0.0731 | 0.0584 / 0.0574 | 0.0985, 0.97 (3,915, 348) | 0.0653, 1.16 | 0.0754 | 1.055 |
| buildings | 0.0790 ± 0.0042 | 600 | 0.0790 | 0.0200 / — | 0.0257, 0.65 (2,279, 35) | 0.0755, 0.90 | 0.0760 | 0.785 |
| contents | 0.0089 ± 0.0020 | 300 | 0.0387 | 0.0799 / 0.0724 | 0.0397, 1.70 (2,869, 64) | 0.0383, 1.07 | 0.0416 | 1.070 |

Reading. Scores are far below Part 1's (hundreds of thousands of rows there): with 3,500 motor claims and ~500 property claims per year, the fold D² is itself noisy, and the buildings score moves by 0.004 between seeds. The new-business subset scores better than the renewal subset in motor (a cleaner frequency signal from age/licence) and is at the overall level in contents; in buildings 35 claims make the subset unreadable.

Pre-registered feature-group tests (Δ D² vs lean on the primary fold at the chosen rounds; secondary in brackets where run):

| group | motor | buildings | contents | decision |
|---|---|---|---|---|
| channel + payment_method | −0.0001 (+0.0011) | −0.0009 (+0.0047) | +0.0053 (+0.0007) | not adopted: within noise in motor and buildings; contents gain is 2.6 sd on the fold but nil on the secondary |
| marketing (email, consent, document, previous_insurer, branch, segment) | +0.0018 (−0.0021) | −0.0573 (−0.072) | −0.0205 (−0.020) | not adopted: destroys property (40-level previous_insurer, 25 branches over-fit); inconsistent in motor — confirms R-0302 |
| make_model + vehicle_colour | −0.0141 | — | — | not adopted: 300 codes over-fit at this volume |
| weather address means | −0.0001 | −0.0021 | −0.0029 | not adopted: no gain, as in Part 1 |
| gender | +0.0023 | +0.0007 | +0.0027 | not adopted in the baseline: 3.8 sd in motor, 1.4 sd in contents, within noise in buildings; use is a rating-rule decision for the team |

Deviance decomposition on the primary fold (R-0107): share of model deviance from zero-claim rows / ordinary claim rows / top-1% claim rows: motor 57% / 34% / 9%, buildings 58% / 32% / 10%, contents 50% / 44% / 6%. Frequency discrimination dominates, as in Part 1; a severity refinement can move at most the ordinary-claim third, and the top-1% rows are a tenth of the deviance that no row feature will explain.

Segment actual/expected on the primary fold (2023 model on 2024, before the cap multiplier; claims in brackets):

| segment | motor | buildings | contents |
|---|---|---|---|
| age 17-24 / 25-34 / 35-49 / 50-64 / 65+ | 1.02 / 1.40 / 0.83 / 0.97 / 1.33 (790 / 697 / 385 / 391 / 801) | 0.61 / 0.49 / 1.08 / 1.25 / 1.10 (101 / 100 / 74 / 75 / 164) | 1.56 / 1.20 / 0.67 / 1.16 / 1.00 (129 / 99 / 51 / 73 / 135) |
| channel broker / comparison / direct | 1.12 / 1.21 / 1.18 | 0.94 / 1.15 / 0.66 | 1.16 / 0.98 / 1.05 |
| new business / renewals | 0.97 / 1.16 (348 / 2,716) | 0.65 / 0.90 (35 / 479) | 1.70 / 1.07 (64 / 423) |
| tenure 0 / 1-2 / 3-7 / 8+ | 0.97 / 1.10 / 1.03 / 1.25 | 0.65 / 0.61 / 1.04 / 0.93 | 1.70 / 1.01 / 1.08 / 1.08 |
| post-mid-term-change rows (R-0309) | 1.23 (143) vs 1.13 others | 0.26 (8) | 2.18 (14) |

What is readable: motor 2024 ran 14% above the 2023 model before the multiplier (5.5% after), with the gap concentrated in 25-34 and 65+ and in long-tenure renewals; buildings 2024 ran 21% below (fire, target_notes §5) with the under-35 bands over-predicted; contents new business ran 70% above the model on 64 claims. The post-mid-term-change bias Part 1 saw (over-prediction) is not reproduced in motor, where those rows are under-predicted by 23% on 143 claims; property counts are too thin to say. None of these is applied as a correction (one fold; R-0307), but the contents new-business gap is the one most likely to be real: training new business ran 31% above renewals raw and 29% age-standardised, and 2023 new policies stayed 25% above other renewals in 2024 (shift_report §5).

## 4. Predicted level by line against history (R-0208, R-0501)

| line | raw burning cost 2023 / 2024 (at valuation) | completed 2023 / 2024 | completed and trended to 2025 | candidate A test level (new business / renewals) | candidate B (zero trend) | max prediction A |
|---|---|---|---|---|---|---|
| motor | 432.7 / 382.7 | 443.8 / 460.7 | 470.8 / 474.5 | 562.2 (598.6 / 441.2) | 538.0 | 1,155 |
| buildings | 514.3 / 306.7 | 515.3 / 323.7 | 578.9 / 343.1 | 389.8 (389.6 / 390.7) | 357.8 | 7,737 |
| contents | 91.1 / 86.8 | 91.3 / 89.5 | 100.6 / 93.9 | 91.7 (92.4 / 89.4) | 85.4 | 643 |

`tools/check_sub.py --cleaned` passes for both files (209,063 rows, ids identical to the sample, no nulls, no negatives) and prints the raw history above; the gap between the printed history and the prediction is explained line by line:

- Motor: the predicted level is 30% above the raw 2024 history and 19% above the completed, trended training level because three quarters of the 2025 exposure is new business, which the model prices 36% above renewals (training new business ran 59% above renewals raw and 18% above after age standardisation; the model's figure sits between because it also carries the younger age mix). Of the 30%: completion +9%, trend +3%, new-business mix +18%.
- Buildings: the predicted level is 27% above raw 2024 and 25% below completed, trended 2023; it sits near the 2024 year because the test book is younger and the model's under-35 relativities are low (fold A/E 0.5-0.6 for those bands) and because the model finds no new-business effect; the two training years disagree by 70% on level (fire), and the model's intercept is the pooled, cap-redistributed middle. The level carries ±15% from the fire year mix alone.
- Contents: the predicted level is 6% above raw 2024 and 5% below the trended training level because the model gives new business almost no uplift (+3%) while the data say +30% (two years, 102 claims; fold A/E 1.70 on 64 claims). If the team adopts a shrunk new-business uplift of +15-20% on the 76% new-business rows, the contents level rises to about 103-106 CU per exposure-year.

Both candidates were validated on the same fold (the trend only rescales the level: candidate B is candidate A divided by 1.044 / 1.087 / 1.073, nothing else changes). Recommendation: candidate A. The developed market's completed cost grew 3-6% a year over 2021-2023; the one emerging step (2024/2023 completed) is +4% in motor; B is the file to choose if the team reads the developed 2024 flattening as real rather than as under-reserving.

## 5. holdout_2024.csv

59,202 rows (motor 25,603, buildings 14,867, contents 18,732), one per 2024 training row, from the same code path as the submission with the training set restricted to 2023 rows (no 2024 row, no developed data). Prediction = rate × exposure × completion × 1/trend_factor_2024 × cap multiplier, i.e. the expected cost reported by 31 Dec 2024. Totals: motor 7.29m predicted vs 7.69m observed (A/E 1.055), buildings 4.73m vs 3.71m (0.785), contents 1.21m vs 1.30m (1.070); D² 0.0754 / 0.0760 / 0.0416.

## 6. What this baseline does not do

No blend, no credibility, no segment correction, no IBNER uplift, no developed-market folds as a direction check, no hyper-parameter search beyond the pre-registered round counts. Each is listed with its expected size in `adaptation_decisions.md`; the largest open levers are the contents and motor new-business levels and the buildings fire load, not model shape.
