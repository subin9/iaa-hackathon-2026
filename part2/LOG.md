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
