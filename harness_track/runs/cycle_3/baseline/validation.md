# Baseline model — validation note

Files: `submission.csv` (borrowed trend applied: motor 0%, buildings +6%/yr, contents +5%/yr over
1.5 years), `submission_no_trend.csv` (same model, no trend), `holdout_2024.csv` (every 2024
training row of all three lines, from models trained on 2023 rows only, on the reported-at-valuation
basis = ultimate × completion). Script: `work/p40_baseline.py`; results: `work/baseline_results.json`.
Both submission files pass `tools/check_sub.py`.

## 1. Model

Per line, LightGBM Tweedie (power 1.5), 3 leaves, learning rate 0.02, extra_trees, min_data_in_leaf
100, L2 1.0, feature_fraction 0.9, categorical smoothing (cat_smooth 20, cat_l2 10, min_data_per_group
100), **max_delta_step 0.7** (added after the first run, see §4), 6 threads, 3 seeds averaged.
Offset `log(exposure × completion)` with the init score set to the training capped-level
(R-0311). Target `y_capped` (99th percentile cap, target_notes.md §5); predictions multiplied by the
cap multiplier (1.078 / 1.119 / 1.053) and by an explicit level factor (§4).

Lean feature set (R-0302): policy risk factors, tenure (`new_business`, `renewal_count`,
`discount_applied`), customer risk attributes (gender, occupation, marital status, household size,
prior claims, licence points, years at address), `region`, `urban_density` and — for property — the
address attributes. Excluded: weather, channel, marketing/campaign/email/document/previous-insurer/
branch, `days_quote_to_inception`, `missed_payments_12m`, `make_model` (300 levels on 7k claims),
`vehicle_colour`, premium, all `x_*` and `dq_*` columns. Developed data was not used for training.

## 2. Validation design (and where the playbook could not be applied as written)

| Rule | As written | Here | What is weaker |
|---|---|---|---|
| R-0201 time-ordered folds | train ≤ Y−1, predict Y; Part 1 had 3 folds | **one fold: 2023 → 2024**, plus a policy-grouped 3-fold within 2023–24 as a labelled secondary check | a single fold whose training year is a survivor sample (F-10) and whose target year is 80% / 94% / 97% complete |
| R-0202 adopt only if every fold improves > noise floor | 3 folds, +0.0003 | one fold + grouped check must agree in direction; developed folds not re-run | direction checks only; no change beyond the pre-registered grid was adopted |
| R-0203 seeds | ≥3 seeds | 3 seeds on every number | — |
| R-0312 capacity grid | half / default / double with edge rule and floor | grid {150, 300, 600} at lr 0.02; edge → 100 (floor) or 2400; smaller count only if the secondary agrees | — |
| R-0406 new-business subset | score on NB subset | reported next to overall | NB subset of 2024 has 382 / 37 / 65 claims |
| R-0204 public-leaderboard noise | pairwise 0.0009 on 207k rows | not measurable here; test is 209k rows so a similar 0.001 should be assumed | — |

## 3. Scores (Tweedie D², power 1.5, 3-seed means; seed sd in brackets)

Primary fold 2023 → 2024 (prediction = ultimate × completion of the 2024 row):

| Line | 150 rounds | 300 | 600 | edge test | chosen | D² on new-business subset (chosen) | Secondary grouped OOF D² (1 seed) at 150 / 300 / 600 |
|---|---|---|---|---|---|---|---|
| motor | 0.0721 (0.0003) | 0.0751 (0.0003) | **0.0765** (0.0001) | 2400: 0.0694 | **600** | 0.0965 | 0.057 / 0.062 / **0.063** |
| buildings | 0.0354 (0.0005) | **0.0425** (0.0018) | 0.0409 (0.0020) | — | **300** | 0.005 (37 claims) | 0.059 / **0.063** / 0.057 |
| contents | 0.0653 (0.0004) | 0.0580 (0.0010) | 0.0429 (0.0020) | 100 (floor): 0.0664 | **300** | 0.0797 | 0.064 (100) / 0.068 / **0.075** / 0.074 |

Contents: the primary fold preferred the 100-round floor, the grouped check preferred 300; per the
R-0312 guard the smaller count was not adopted. Motor and buildings: both checks agree.

Lean vs full feature set at the chosen rounds (primary fold): motor 0.0765 vs 0.0574, buildings
0.0425 vs 0.0272, contents 0.0580 vs 0.0507 — lean wins on all three lines by more than the seed sd,
confirming the Part 1 finding (R-0302) in this market. Full-set gains on the new-business subset
(contents 0.110 vs 0.080) are noted but not adopted on one fold.

Noise floor observed: seed sd 0.0001–0.0003 (motor), 0.0005–0.0020 (property). Property differences
below ≈0.004 should be read as noise.

Deviance decomposition on the 2024 fold (R-0107): zero-claim rows carry 58% / 68% / 56% of the
deviance (motor / buildings / contents), ordinary claims 33% / 24% / 39%, the top 1% of claims
9% / 9% / 5% — frequency discrimination dominates, as in Part 1.

## 4. Level gate (R-0311)

After fitting, Σ prediction / Σ target on the **training** rows (before correction):

| Line | 2023-only model (chosen rounds) | final 2023+2024 model (3 seeds) | explicit level factor applied |
|---|---|---|---|
| motor | 0.954 | 0.969 / 0.969 / 0.970 | ×1.032 |
| buildings | 0.803 | 0.869 / 0.868 / 0.868 | ×1.152 |
| contents | 0.848 | 0.889 / 0.889 / 0.890 | ×1.125 |

The first run (no leaf-step guard, make_model included, grid 300/600/1200) lost 7–40% of the level
and D² fell with rounds (motor 0.059 → 0.036); the guard and dropping make_model recovered most of it
(motor D² 0.077). The remaining shortfall is the known small-data behaviour of a shallow, regularised
Tweedie booster; the factor restores the training level exactly and is reported here rather than
hidden. A GLM-style intercept refit would make the factor unnecessary.

## 5. Holdout 2024 (models trained on 2023 only; reported basis)

| Line | Rows | D² | Σ pred / Σ actual | Predicted ultimate per exposure-year (2024 rows) | Actual 2024 ultimate (target_notes §7) |
|---|---|---|---|---|---|
| motor | 25,603 | 0.0766 | 0.914 | 437 | 478 |
| buildings | 14,867 | 0.0427 | 1.559 | 508 | 325 |
| contents | 18,732 | 0.0582 | 1.042 | 93 | 89 |
| all | 59,202 | | 1.116 | | |

Reading: motor 2024 ran 7% above 2023 on an ultimate basis and the 2023-trained model sits 9% low;
buildings over-predicts by 56% because 2023 was the fire year (49 fires vs 21); contents is within 4%.

Actual / predicted by pre-registered segment on the 2024 fold (R-0307; one fold, no correction applied):

| Segment | motor | buildings | contents |
|---|---|---|---|
| new business / renewal | 0.89 / 1.12 | 0.50 / 0.66 | 1.43 / 0.92 |
| age 17-24 / 25-34 / 35-49 / 50-64 / 65+ | 0.99 / 1.28 / 0.81 / 0.95 / 1.32 | 0.45 / 0.37 / 0.74 / 0.87 / 0.81 | 1.36 / 1.03 / 0.58 / 0.99 / 0.84 |
| channel broker / comparison / direct | 1.08 / 1.16 / 1.12 | 0.69 / 0.87 / 0.46 | 1.00 / 0.83 / 0.88 |
| payment annual / monthly | 0.96 / 1.25 | 0.59 / 0.70 | 0.81 / 1.14 |

New-business relativity (R-0410): pre-model, age-standardised cost ratio new/renewal = 1.43 (motor),
0.82 (buildings, thin), 1.23 (contents). The 2023-only model implied 1.59 / 1.04 / 0.97 against the
2024 actual 1.27 / 0.79 / 1.51. The final 2023+2024 model prices the 2025 book at 1.48 (motor:
624 vs 421 per exposure-year), 1.00 (buildings) and 1.02 (contents). Motor is consistent with the
pre-model figure; **contents is priced flat against a 1.2–1.3 signal on 102 claims** — the R-0410
failure mode; a decision for the team (adaptation_decisions.md, open decision 2).

## 6. Predicted level against history (R-0208, R-0507)

`check_sub` printout, predicted CU per exposure-year on the 2025 test rows vs training-year burning
cost (raw, at the valuation date, no completion adjustment):

| Line | Predicted (trend file) | Predicted (no-trend file) | History on **as-delivered** tables 2023 / 2024 | History on **cleaned** tables 2023 / 2024 | Ultimate (completion-adjusted) 2023 / 2024 |
|---|---|---|---|---|---|
| motor | 576.9 | 576.9 | 307.7 / 275.8 | 432.7 / 382.7 | 447 / 478 |
| buildings | 467.5 | 428.4 | 312.0 / 246.7 | 514.3 / 306.7 | 515 / 325 |
| contents | 99.4 | 92.4 | 70.0 / 63.2 | 91.1 / 86.8 | 91 / 89 |

The raw-vs-cleaned difference is the exposure repair alone: the day-count rows inflated the
as-delivered exposure by 40% (motor), 44% (buildings), 34% (contents), so the as-delivered history
understates every burning cost by that much. Maximum predictions 1,615 / 5,588 / 637.

One sentence per line on the gap between prediction and (cleaned, ultimate) history:

- **Motor** 577 vs 447–478: the 2025 book is 76% new business and the model's new-business relativity
  is 1.48 (pre-model 1.43), so the level is 21% above the renewal-dominated training years by
  construction; if the acquired book behaves like renewals the right level is ≈480.
- **Buildings** 428 (468 with trend) vs 515 / 325: the model averages a fire-heavy and a fire-light
  year; the trend file adds the borrowed +6%/yr.
- **Contents** 92 (99 with trend) vs 91 / 89: level as history, new business priced flat (see §5).

## 7. Reconciliation ladder (R-0017)

| Link | Raw → cleaned / check | Status |
|---|---|---|
| Exposure-years (motor / buildings / contents) | 54,429 / 33,783 / 38,893 → 38,969 / 23,468 / 29,058; explained by F-01 (114 rows, −35,605) and F-02 (495 rows, −4.9) | closed |
| Claims count | 9,258 → 9,222 (−36, F-08) | closed |
| Net incurred | 28,090,258.83 → 27,997,991.57 (−92,267.26, F-08) | closed |
| Σ y modelling tables vs cleaned claims | 27,997,991.57 = 27,997,991.57 | closed |
| Model level Σ pred / Σ target on training rows (after factor) | 1.000 by construction; factors 1.032 / 1.152 / 1.125 reported | closed, factor reported |
| Holdout Σ pred / Σ actual 2024 | 0.914 / 1.559 / 1.042 — explained by the 2024/2023 level change (motor +7%, buildings −37% fire year, contents −2%) | explained, not an error |

## 8. Candidates for the human (R-0505)

Two files that differ only in the trend assumption (buildings +9.1%, contents +7.6%, motor none):
`submission.csv` (trend) and `submission_no_trend.csv`. The larger unvalidated level questions —
motor new-business relativity (±21%) and contents new-business relativity (+17%) — are not expressed
as files; they are listed as open decisions and can be applied as line/segment factors before
submission. Nothing has been submitted.
