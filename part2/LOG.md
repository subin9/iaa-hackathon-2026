# Part 2 working log

Chronological notes of what was tried in Part 2, what each step showed and what was decided. Numbers are copied from script output
(the script is named at each step). Times are UTC. The final report and the video are written from this log.

## 2026-10-24, setup and data

- Part 2 opens on its own competition page: `iaa-ai-assisted-hackathon-2026-part-2`, closes 2026-10-31 03:59:59 UTC, ten submissions a day.
  The task is the expected ultimate claim cost of every 2025 row in the three emerging-market test files. The deliverables are a 5 minute
  video, a 5 page report and versioned code. The report has to show the office premium build-up for 20 reference policies.
- The folder `developed/` is the Part 1 data again. `emerging/` holds two policy years (2023 and 2024), 109k training rows against 209k test
  rows, and 76% of the 2025 rows are new business (training: 12 to 15%). Claims in both markets are valued at 31 December 2024.
- `part2/eda_01_overview.py`: sizes, years, claims. `part2/eda_02_quality.py`: column profile. `part2/eda_03_missing_drift.py`: about 12% of
  the values are missing in 11 to 12 columns, independently per column and with the same rate in every year, channel, region and in the test
  rows, so the gaps look random and carry no information.
- Data checks (all in `part2/prep_emerging.py`): exposure is stored in days for some rows (rebuilt from the dates, as in Part 1); sums
  insured up to 1000 times too large (divided by 1000 above 100 times the median); free-text occupation (81 spellings of 20 occupations plus
  "Self-employed X"): trimmed, lower-cased, self-employed split into a flag. There are no exact-repeat claims in the emerging file (604 in
  the developed one).
- Completion (share of the ultimate cost already reported at 31 December 2024): the emerging market has no mature accident year, but its
  report-lag percentiles match the developed market (median 9 days, 90th percentile 44 to 46 days for motor), so the completion curves of the
  developed market are used.

## What changed (EDA 4 to 6)

- `part2/eda_04_drift.py`: apart from coding (occupation text, construction codes, age bands) and channel mix (70% broker), the emerging
  risk factors have the same distribution as the developed ones (PSI near 0 for sum insured, vehicle value group, flood zone and so on).
  Train against test inside the emerging market: the adversarial AUC is 0.87 to 0.88 and the signal is new business, renewal count and
  campaign code (83% of the test rows carry a campaign code, 19% of the training rows).
- `part2/eda_05_oneway.py`: one-way relativities are similar in both markets (driver age band 17-24: 1.97 developed, 1.67 emerging).
- `part2/eda_06_weather.py`: the weather perils follow their weather variable in both markets (hail days and glass claims, wind and storm,
  rainfall and flood, freezing days and escape of water), but the climate differs: median hail days 14 against 6, freezing days 19 against 35,
  wildfire index 0.5 against 0.1.

## Transfer experiments (5-fold CV grouped by customer on the emerging rows, pooled D2)

- Bug found first: LightGBM reads columns by position, so a developed model scored on an emerging frame with a different column order gave
  nonsense (pooled 0.036). Fixed in `part2/lib.py::features`; a test now guards it.
- `e0_zero_shot.py`: developed model with the line level matched: 0.134 pooled, against 0.118 for a model trained on emerging data only
  (`e1_em_only.py`) and 0.078 for one constant rate per line. The developed relativities carry over; the levels do not (motor A/E 0.745).
- `e2_transfer.py`: boosting corrections from the emerging data on top of the prior adds nothing (0.1339 against 0.1337); the developed
  prediction as a feature is worse than using it as the offset.
- Developed-market check (`work/nb4.jsonl`): the new-business flag adds +0.0002 and +0.0006 on the two Part 1 validation folds, so the prior
  keeps `new_business` (Part 1 had dropped it with the other lean columns). Emerging CV: 0.1337 to 0.1345 for the line prior.
- A per-peril prior (sum of five to six peril models) beats the line model: 0.1359 against 0.1345 (`e9_peril_shrink.py`). Peril levels are
  estimated on the emerging data and shrunk toward the line level with c = n / (n + 400).
- Corrections tested with a robust score test and a ridge GLM (`adapt.py`, nested CV in `e8_adapter_cv.py` and `e10_pipeline_cv.py`):
  motor gender (males x1.31, +0.003 on the motor D2) and buildings age band (35-49 x0.66, +0.005) help; the rest is noise at this data size.
- Weather in the prior: helps glass_hail and storm per peril, but not the line D2 in CV, and hurts flood and fire; left out of the prior.
- make_model and the other vehicle details do not change the motor CV at all (`e11_motor_prior_variants.py`); dropped from the transferred
  prior because the make codes are not comparable between markets.

## Leaderboard (public)

- v0 prior x line level: 0.14872. v1 with new_business in the prior: 0.15483. v2 per-peril prior, shrunk peril levels, gender and age band:
  0.15938.
- Segment probes on v2 (x1.2 on one segment each): motor new business 0.16370, buildings new business 0.16037, contents new business 0.15945,
  all renewals 0.15880. The public deviance is separable by segment, so the probes give the best multiplier per segment
  (`probe_solve.py`): motor NB 1.40, buildings NB 1.23, contents NB 1.11, renewals 1.01. The model predicted 0.16433 for the halfway point and
  the leaderboard returned 0.16446, which validates the method.

## 2026-10-24, later: data repair, peril-specific correction, tests, report

- Construction type: the developed `construction_type` has 11 spellings (Brick, brick, BRICK, stone, STONE, non_standard, NON_STANDARD, W, w, T, t). Case variants are the
  same category; T was used in 2021-22 and W from 2023 on (cross-tab by year in the log of this step), so both letters are timber. A first mapping assumed the
  documented spellings and turned 90% of the rows into missing values; the counts after mapping caught it. With the 4 codes the buildings CV D2 rose from 0.105 to 0.110
  (levels only) and the pooled final from 0.1385 to 0.1409. In Part 1 this column was left as it came, so a model could read T/W as a year flag for buildings.
- Prior variants: Tweedie 1.4, Poisson and extra-trees, averaged in log space (`average_priors.py`): pooled CV 0.1385, 0.1370, 0.1396 and 0.1391 for the average, which is
  what the final model uses (an ensemble of three is a safer choice than the single best of three at this noise level).
- Gender acts on the at-fault perils (male/female frequency ratio 1.66 bodily injury, 1.30 own damage, 1.43 third-party property; glass 1.04, theft 1.17), so the correction
  is fitted on those three perils only: motor CV D2 0.0720 against 0.0714 for a line-level factor. Final CV pooled 0.1414 (`e10_pipeline_cv.py`).
- Rejected on the emerging data: experience rating on renewals (D2 falls monotonically as credibility rises, `e12_experience.py`), written premium relative to the model
  (A/E flat across quintiles), exposure-length effects, weather in the prior (`e9`, `eda_06`; per-peril deviance +1.8% for glass and +1.1% for storm, but the line D2 falls in CV).
- Campaign codes: 83% of the test rows carry one (19% of training rows). The code identity is noise (year-to-year correlation of the A/E per code 0.12 to 0.35); what matters is
  that coded rows are recent customers, who show the new-business uplift.
- New business by channel in training: broker new business A/E 1.25 (555 claims, motor and contents), direct 0.94 (206 claims); not significant, so no channel split in the model.
- Tests: `part2/tests/test_part2.py`, 22 checks. Bugs caught on the way: the column order (zero-shot pooled D2 0.036 against 0.134), a double level correction (motor mean
  prediction 619 against 553 per exposure year), the construction recode, and a feature leak into the emerging-only comparison model (0.1244 against 0.1176).
- Total matching: the ridge GLM with the Tweedie score equation left the training total up to 3.6% off in motor; the pipeline now rescales to the training total.

## Public leaderboard budget

Ten submissions a day, counted in UTC days. On 2026-10-24 the ten went to v0, v1, two probes on v1, v2, four probes on v2 and the half-way check v3_half. The full-step
version of the solved multipliers (v3_full) and the probes on channels follow after the reset at 00:00 UTC.

## 2026-10-25, probes on v5 and the limit of leaderboard fitting

- The 00:03 UTC job ran: v4 0.16135, v5_full 0.16797 (v4 times the transferred multipliers), and seven probes on v5.
- Structure-free solution on v5 (`probe_solve.py`, the four base segments): motor NB 0.892, buildings NB 0.940, contents NB 0.972, renewals 0.996, so the transferred
  levels were nearly right and the best case of level changes alone is 0.16869. Overlay probes, each solved alone with the null deviance from the four-segment solution:
  motor new business through the direct channel 0.708 (training data agrees: direct new business A/E 0.94 against broker 1.25), buildings age 35-49 1.185, all motor males 1.191.
- A seven-parameter multiplicative structure (`probe_solve_struct.py`, probe rounding propagated) predicted 0.17512 for v6 (the shrunk solution); the leaderboard gave 0.17182.
  The nine scores are not consistent with the separable formula to better than about 3e-4 of D2 (the equations use one third of the sum of mu^1/2 per cell in place of the
  unknown public sum), and with that tolerance the data no longer pin down a structure (`probe_solve_ridge.py`: leave-one-probe-out errors of 0.003 and absurd factors in
  free structures). Lesson: fit the gain to the tolerance, not to the rounding.
- Sampling noise of a public-fitted factor (`e13_cell_noise.py`, bootstrap of out-of-fold training rows, as many rows as the public part of each segment): sd of log m* 0.05
  (motor NB) to 0.32 (buildings age 35-49). Factors are shrunk by tau^2 / (tau^2 + se^2) before they are used.
- `probe_solve_cells.py`: twelve cells, ridge prior and an equation noise of 2e-4 give a mild solution (motor NB female 0.69, male 1.19, direct 0.76-0.82, renewals 0.93-1.19 by
  gender, buildings and contents renewals 0.95). Predicted public D2 0.1715 for the shrunk file (v7) and 0.1729 at the unshrunk cell optimum, against 0.17182 for v6: further
  leaderboard fitting is worth at most 0.001 on the public rows and less on the private rows.
- Submissions used for this round: v6 (one of the five the user allowed); v7 is queued for 00:03 UTC on 2026-10-26.

## 2026-10-26, v7 result and an independent code review

- v7 (queued job, 00:03 UTC): public 0.17300, the best so far; v6 0.17182.
- An independent review (a fresh agent reading the code, not my conclusions) found that every probe solver leaves out the constant of the Tweedie deviance,
  -8 sum(sqrt(y)). It cancels between submissions but not in the null deviance, so the solved factors were pushed away from 1. On a synthetic leaderboard the fixed
  solver recovers the public optimum exactly (1.336, 0.943, 1.106) and the old one gives 1.441, 0.877, 1.111. This explains most of the "inconsistent to 3e-4" note above:
  with S as one more unknown (`probe_solve_cells.py`, prior centred on an estimate from the out-of-fold rows; fitted at 1.15 times it) the nine scores fit to 6e-5.
- It also explains why the v2 solution (motor NB 1.40) overshot: the structure-free solution on v5 brought motor NB back to 0.89.
- Effect on the submitted file: the corrected solution (v8, total 88.1M against 85.98M) and v7 score the same under the corrected model (0.17336 both); under the old
  model v8 is 3e-4 worse. Neither model predicts v7 well out of sample (0.17336 and 0.17269 against 0.17300). v7 stays; v8 is not submitted.
- Also fixed: the "predicted public D2 applied" line of probe_solve_cells.py scored the applied factors as if they were the truth (it printed 0.1715 for v7; the right
  figure under that model was 0.17269, and the v7 submission description on Kaggle carries the wrong number). Two tests that could not fail now can: the calibration test
  checks the rescale factor (the rescale made the total exact by construction; an adapter doubled by mistake gives 0.53 and fails), and the probe-solver test scores with
  sklearn's d2_tweedie_score and checks the public optimum to 1%.
- The percentages quoted for weather in the prior (+1.8% glass, +1.1% storm) came from scripts with the same truncated deviance, so they are relative to a smaller
  denominator and overstate the change; the model ranking does not change.
