# Baseline model — validation note

Script: `work/c04_baseline.py` (one code path `fit_predict` for the validation fold, `holdout_2024.csv` and the submission). Statistics: `work/baseline_stats.json`. Inputs: `outputs/modelling_tables/`. Seeds 0, 1, 2; 6 threads; LightGBM 4.7.0.

## 1. Model

LightGBM Tweedie (power 1.5), 3 leaves, learning rate 0.02, 600 rounds, extra_trees, bagging/feature fraction 0.9, `min_data_in_leaf` 300, `lambda_l2` 20, `max_delta_step` 0.5; nominal categoricals split one-vs-rest (`max_cat_to_onehot` 64), ordered factors (age band, energy rating, security level, urban density, cover type) as integer codes. Offset: `init_score = log(exposure × completion × level)` with level = Σ y_cap ÷ Σ (exposure × completion) on the training rows (R-0311). Target `y_cap` (99th-percentile row cap); prediction = exp(raw) × level × exposure × level factor × cap multiplier (1.078 / 1.119 / 1.053) × trend^horizon. Seed-averaged on the raw score over 3 seeds.

Feature set (lean, R-0302): policy and risk attributes, customer history and household columns, address attributes, `written_premium`, `missed_payments_12m`, `new_business`, `renewal_count`, `tenure_years` — 37 / 36 / 37 features. Excluded: `x_*` stamps and leaks (F-11…F-13), `dq_*` flags, `make_model` (300 levels vs 7k claims; tested, −0.003 D²), the channel/marketing/calendar group (tested, see §4), yearly and mean weather, `compulsory_excess` (constant), `gender` (regulatory question, not tested).

## 2. Validation design and where the playbook could not be applied as written (R-0206)

| Rule | As written | Here | What is weaker |
|---|---|---|---|
| R-0201 time-ordered folds | train ≤ Y−1, predict Y; 3 folds in Part 1 | **one** fold: train 2023 → predict 2024, scored on the reported basis (ultimate × completion vs observed y). 2023 is a survivor sample (F-20): the model learns from policies that all renewed and predicts a 2024 book that includes the 15% that later lapsed. Secondary: policy-grouped 5-fold within 2023–24 (1 seed), labelled weaker because it mixes years. | No replication across folds; the fold's actual/predicted carries the 2023→2024 level change (motor +5%, buildings −42% from fire, contents −12%) that no model could know. |
| R-0202 adoption on every fold beyond noise | ≥ 2 folds, +0.0003 each | primary fold (3-seed mean) must improve by > 0.001 **and** the grouped check must agree in direction; developed-market fold (2021–22 → 2023, 1 seed) used as a direction check only | The local noise floor is unknown; 0.001 is Part 1's single-seed noise, used as a conservative bar. |
| R-0203 ≥ 3 seeds | 3 seeds | 3 seeds on the primary fold, holdout and submission; 1 seed on the grouped and developed checks | grouped/developed numbers carry ±0.001 seed noise |
| R-0312 capacity grid with edge rule and floor | half/default/double | 300 / 600 / 1200 at lr 0.02; edge re-test and 100-round floor coded | The emerging fold prefers 300 for motor and contents, the grouped check prefers 600, so 600 stands; the developed market prefers 1200 (20× the claims) and is not used for capacity. |
| R-0311 level gate before any score | Σ pred ÷ Σ target within a few percent, else fix the learner | first run: gates 0.94 / 0.75 / 0.80 with make_model and raw categoricals (noise fitting; D² fell with rounds). After the fixes in §1: **0.979 motor, 0.882 buildings, 0.894 contents** on the full training set (0.968 / 0.796 / 0.846 on the 2023-only fit). Residual gap closed by an explicit level factor (1.022 / 1.134 / 1.119 on the submission fit), reported here. | The home-line learners still lose 11–20% of level before the factor: with ~1,000 claims a log-link booster at this capacity under-shoots; the factor restores the training level exactly but the relativities are those of an under-levelled fit. |
| R-0204 public-leaderboard noise | known from 33% of 627k rows | not available; nothing submitted | — |
| R-0205 blend | equal-weight blend | single family, seed-averaged (R-0305: fewer members with small data) | no diversity gain |
| R-0207 fix the candidate set first | — | segments (new_business, age band, channel, cover_type/occupancy/tenure), optional groups (make_model, channel+marketing) and the rounds grid were written into the script before the fold was run | — |
| R-0208 level vs history | — | §5 below, on raw and cleaned history (R-0507) | — |

## 3. Scores (Tweedie D², power 1.5, reported basis)

| Line | Fold 2023→2024, 300 / **600** / 1200 rounds (3 seeds) | Fold: new-business subset / renewal subset (600) | Fold actual ÷ predicted | Grouped 5-fold 300 / 600 / 1200 (1 seed) | Developed fold 2021–22→2023, 300 / 600 / 1200 (direction only) | Holdout (= fold, 600) |
|---|---|---|---:|---|---|---|
| motor | 0.0724 / **0.0710** / 0.0678 | 0.0897 / 0.0641 | 1.053 | 0.0602 / 0.0605 / 0.0583 | 0.0705 / 0.0748 / 0.0784 | 0.0710 |
| buildings | 0.0301 / **0.0306** / 0.0270 | −0.040 / 0.0274 | 0.578 | 0.0722 / 0.0643 / 0.0423 | 0.1048 / 0.1090 / 0.1103 | 0.0306 |
| contents | 0.0748 / **0.0718** / 0.0622 | 0.0983 / 0.0666 | 0.883 | 0.0922 / 0.0966 / 0.0946 | 0.0865 / 0.0921 / 0.0936 | 0.0718 |

Reading: motor and contents reach the developed market's out-of-year D² on 1/20 of the claims; buildings does not (0.03 vs 0.11): one year of 520 claims dominated by fire does not predict the next. The new-business subset scores higher than the renewal subset in motor and contents (R-0406) because its mean is higher, not because it is better understood — see §6. D² falls with rounds on the time fold in all three lines (over-capacity for the year-to-year signal) while the developed market still gains; capacity re-chosen per R-0312 and left at the default because the secondary check disagreed with 300.

Deviance decomposition on the fold (R-0107): zero-claim rows carry 59% (motor), 69% (buildings), 58% (contents) of the deviance; ordinary claims 32 / 22 / 38%; the top-1% claims 9 / 9 / 4%. Frequency discrimination dominates, as in Part 1; a severity refinement cannot move the score much.

Optional feature groups on the primary fold (600 rounds, 3 seeds): `make_model` −0.0029 (motor; excluded); channel + marketing group +0.0003 motor (noise), +0.0020 buildings, +0.0039 contents. Not adopted: one fold, and Part 1 found these groups hurt out-of-year; recorded as the first thing to re-test when a second fold exists.

## 4. Segment actual ÷ predicted on the fold (600 rounds; candidates fixed before looking)

| Segment | Motor A/P | Buildings A/P | Contents A/P |
|---|---|---|---|
| new_business = false / true | 1.09 / **0.81** | 0.60 / 0.40 | 0.84 / **1.39** |
| age band 17–24 / 25–34 / 35–49 / 50–64 / 65+ | 0.91 / 1.28 / 0.82 / 0.94 / 1.26 | 0.41 / 0.33 / 0.47 / 0.90 / 0.78 | 1.13 / 0.90 / 0.54 / 1.00 / 0.81 |
| channel broker / comparison / direct | 1.03 / 1.12 / 1.09 | 0.62 / 0.76 / 0.43 | 0.91 / 0.77 / 0.83 |
| cover_type TPO / TPFT / comp — occupancy let / owner — tenure owner / renter | 0.93 / 0.68 / 1.13 | 1.39 / 0.49 | 0.85 / 0.96 |

With one fold, none of these qualifies for a correction (R-0307 needs the same direction on every fold). The new-business row is the one that matters for 2025 (§6).

## 5. Predicted level against history (R-0208, R-0507)

`check_sub.py` on the as-delivered tables and on the cleaned tables (the difference is the exposure repair alone: +40% on every historical burning cost):

| Line | Predicted CU per exposure-year, 2025 (candidate A) | History on raw exposure 2023 / 2024 | History on cleaned exposure 2023 / 2024 | Completed history 2023 / 2024 | Max prediction |
|---|---:|---|---|---|---:|
| motor | **571.6** | 307.7 / 275.8 | 432.7 / 382.7 | 444.3 / 461.5 | 1,484 |
| buildings | **478.1** | 312.0 / 246.7 | 514.3 / 306.7 | 515.2 / 323.6 | 7,229 |
| contents | **109.9** | 70.0 / 63.2 | 91.1 / 86.8 | 91.3 / 89.5 | 976 |

One sentence per line. **Motor**: 572 is 26% above the completed two-year average (453) because 76% of the test book is new business priced at the model's new-business relativity of 1.47 (training new business ran at 1.67 in 2023 and 1.28 in 2024 on capped completed cost) with a younger age mix; the renewal rows are priced at ≈ 420, close to their history. **Buildings**: 478 is the completed two-year average (417) × the borrowed trend (1.099) with a flat new-business relativity (1.00 vs 0.97 frequency pre-registered); the two years disagree by 60% because of fire, so 320–560 are all defensible. **Contents**: 110 is the completed two-year average (90) × trend (1.074) × a new-business relativity of 1.12 against a pre-registered 1.25–1.33; it is the line most likely under-priced for the acquired book.

## 6. New-business relativity: model vs pre-registered table (R-0410)

| Line | Pre-registered, age-standardised (freq / capped cost) | Observed capped completed cost NB ÷ renewal, 2023 / 2024 | Model on 2024 fold (trained on 2023) | Model on test (trained on 2023–24) |
|---|---|---|---|---|
| motor | 1.17 / 1.24 | 1.67 / 1.28 | 1.68 (over-predicted 2024 NB: A/P 0.81) | **1.47** |
| buildings | 0.97 / 1.18 | 1.11 / 0.84 | 1.18 | 1.00 |
| contents | 1.25 / 1.33 | 1.14 / 1.63 | 0.91 (under-predicted 2024 NB: A/P 1.39) | 1.12 |

The model's relativity is the two-year compromise; the two years disagree by 30–45% in every line on 300–400 (motor) or 40–65 (home) new-business claims. This, not trend, is the main level hypothesis for motor (R-0505).

## 7. Candidate files (R-0505) — the human selects one

| File | Assumption | Motor / buildings / contents CU per exposure-year |
|---|---|---|
| `submission.csv` (A, central) | model as fitted; borrowed trend over 1.49 years (×0.992 / ×1.099 / ×1.074) | 571.6 / 478.1 / 109.9 |
| `submission_notrend.csv` (B) | same model, no trend | 576.1 / 435.2 / 102.3 |
| `submission_nb2024.csv` (C) | A, with motor new-business rows scaled 0.8715 so the motor new-business relativity equals the 2024-observed 1.28 instead of the model's 1.47 | 510.6 / 478.1 / 109.9 |

All three pass `check_sub.py` (209,063 rows, ids match, no nulls or negatives). Reasons to prefer A: it is the data as fitted, and the 2023 new-business experience is as valid as 2024's. Reasons to prefer C: the only out-of-time test available (2023 → 2024) over-predicted new business by 23%, and a transferred broker book is more likely to resemble ordinary new business than the 2023 cohort's large-loss experience (2023 NB uncapped relativity 2.27). B is for a team that does not believe a developed-market trend transfers.

## 8. Holdout file

`holdout_2024.csv`: 59,202 rows (every 2024 training row, all lines), predicted by models trained on **2023 rows only** (3 seeds, 600 rounds, same code path, borrowed trend over 0.99 years), on the reported basis — ultimate × row completion — so it can be scored against the observed `y`. D² 0.0710 / 0.0306 / 0.0718; actual ÷ predicted 1.053 / 0.578 / 0.883. The developed data were not used for training (only for the completion tail, the trend and the direction check).
