# Video material from the modelling track

The team video has six scenes; the teammate keeps the narration script (`narration_scripts.md`, HS voices scenes 1 to 3 and the close,
Evan scenes 4 and 5). This file lists, for every number and claim in the narration, where the repository backs it, and which screen
recording plays behind which line. Every number is copied from `part2/LOG.md`, `part2/probes.json`, `part2/final.json`,
`harness_track/` or script output.

## Narration claims and their sources

| scene | spoken | value in the repository | source |
| --- | --- | --- | --- |
| 1, 3 | fifty rules of method; findings caught by rule fifteen to twenty-three, new ones eight to two | rules 50, 63, 67, 68; rule-caught 15, 17, 23, 23; novel 8, 6, 2, 2 | `harness_track/AI_USAGE.md` (cycle log) |
| 2 | exposure in days, sums insured a thousand times too big, both caught | 114 rows in days (plus 493 on a 360-day basis); 110 train and 239 test rows x1000 | `harness_track/eval/scorecards/cycle_1.md` |
| 2 | a quarter of buildings claims still open | 2024 buildings open share 25.3% of claims, 34.7% of cost | `harness_track/runs/cycle_3/target_notes.md` |
| 2 | the markets report claims at the same speed | motor report lag median 9 days, 90th percentile 44 against 46 | report section 3, `part2/LOG.md` |
| 2 | the harness's own curve agreed within two and a half percent | 2024 completion, harness curve against the developed curve: motor 0.804 / 0.816, buildings 0.941 / 0.926, contents 0.971 / 0.970 (all within 2%); ±2.5% is the motor range over the anchor and cap choices | `harness_track/runs/cycle_3/target_notes.md` |
| 2 | seventy-six percent new business, about a thousand training claims | 76% of the 2025 rows; about 1,000 new-business training claims | report sections 2 and 7 |
| 2 | males about one point four times on the at-fault motor perils, used with a condition | 1.39 (frequency 1.66 bodily injury, 1.30 own damage, 1.43 third-party property); any tariff use needs its own sign-off | report section 2, `harness_track/report/decisions_B.md` (B4) |
| 3 | thirty-six claims dated before their policies began, argued from the report lags | 36 claims, lags 411 to 565 days against a matched 99.5th percentile of 334 days; rule R-0015 from cycle 2 | `harness_track/runs/cycle_4/target_notes.md`, `eval/scorecards/cycle_2.md` |
| 4 | one shallow tree model per peril on the four developed years, levels re-learned on the two emerging years and shrunk | 3-leaf LightGBM per peril on 2021-2024, peril levels shrunk n/(n+400) | report section 4 |
| 4 | corrections pass a robust score test inside each training fold; gender and a buildings age band did | sandwich score test, nested CV; gender (at-fault motor perils) and age band 35-49 survive | report sections 4 and 5 |
| 4 | twenty-two tests before every submission | 22 tests (14 functions, some parametrised by line) | `part2/tests/test_part2.py`, report section 5 |
| 4 | a cold review found a missing constant and two tests that could never fail | Tweedie constant -8 sum(sqrt(y)) missing from the probe solvers; two vacuous tests, fixed and mutation-checked | `part2/LOG.md`, `docs/AI_USAGE.md` |
| 4 | keep-or-drop rules committed to the log before each score | every late submission (v9 onwards) has its rule in `part2/LOG.md` in a commit made before the score came back | `git log -p part2/LOG.md` |
| 5 | 0.059, +0.044, +0.020, +0.007 on one fixed model | 0.05891, 0.10283, 0.12301, 0.13030 | `harness_track/submissions/log.csv`, `harness_track/runs/hs_model/README.md` |
| 5 | my pipeline repairs exposure and sums insured in its first step, as in Week one | exposure rebuilt from the dates, sums above 100x the median divided by 1000 | report section 3, `part2/prep_emerging.py` |
| 5 | the harness caught them by rule, plus two I had missed | the defects the pipeline had not used: nulls refillable from the same policy's other rows, and 2023 as a survivor sample | `harness_track/report/decisions_B.md` ("What this says about the harness") |
| 5 | point one six one with no board information, point one eight after calibration | v4 0.16135; final v14_cells 0.17993 | `part2/probes.json`, `part2/final.json` |
| 5 | office premium two to three times the current tariff | exposure-weighted ratio 2.19 motor, 3.25 buildings, 2.67 contents | report section 9, `work/p2/office_final.csv` |

## Scene 2, pricing and adaptation (more facts if needed)

- Ultimate: developed completion curves; the emerging report lags match (motor median 9 days, 90th percentile 44 against 46).
- Trend: none; two emerging years only, and the fire level alone swung from A/E 3.34 (2023) to 1.10 (2024).
- Transferred broker book: 76% of 2025 rows are new business against 12-15% in training; new-business flag in the prior, then cell levels
  measured on the public board and shrunk for sampling noise (sd of log factor 0.05 to 0.32).
- Measured costs of a 15% level error (public D2, probes on v5 = 0.16797): motor new business -0.00244, buildings new business -0.00085,
  contents new business -0.00035, renewals -0.00043.
- What carried over: rating-factor effects (log correlation of one-way relativities across markets in the report figure). What did not: levels
  (motor 25% lower, bodily injury 0.64, glass 1.28 of the developed model).
- Weather: 22% of the 2025 buildings rows lie above the developed maximum of the wildfire index, where the tree prior is flat; fire takes the
  developed slope (1.66 per unit, from 1,107 developed fires) instead of a slope fitted on 70 emerging fires.

## Scene 5, results

The data-effect ladder (one fixed recipe, `harness_track/runs/hs_model/README.md`) and the modelling track:

| | fixed recipe, no leaderboard information | our pipeline |
| --- | --- | --- |
| competition files | 0.05891 (cell 4) | v9 0.17303 |
| cleaned files | 0.13030 (cell 2) | v10 0.17247 |

Final file: v14_cells 0.17993, first of 38 on 2026-10-30. It averages v9 and v10 (both data versions) with the developed fire slope (v12c,
0.17333) and multiplies fourteen new-business segments by factors measured with disclosed probes and shrunk for noise. Model-only reference:
v4 0.16135 (no leaderboard information). Part 1: private 0.13755, rank 8 of 54.

## Screen recordings

Recorded 2026-10-30 with [VHS](https://github.com/charmbracelet/vhs) from the tapes in `tapes/` (real commands, real output, 1920x1080; the
clips are in `deliverables/video_clips/`, not in the repository):

| clip | length | shows | narration line |
| --- | --- | --- | --- |
| `clip1_tests` | 14 s | the 22 tests passing | scene 4, "twenty-two tests" |
| `clip5_code` | 34 s | the probe solver and its seven factors (first segment round) | scene 4, the cold review (the solver it reviewed) |
| `clip2_rule` | 28 s | the keep rule committed before the v13 scores | scene 4, "keep-or-drop rules committed to the log" |
| `clip3_board` | 16 s | every submission with its score, recorded before the v14 scores (v13_cells at the top) | scene 4 or 5 |
| `clip4_office` | 20 s | office premium build-up for the 20 reference policies, from the final file at recording time (v13_cells) | scene 5, office premium |
| `agent_ide` | 1:08 | editor and a Claude Code agent: the tests, the v14 keep rule committed before its result, and an office premium build-up from v14_cells | scene 4 or 5 |

`all_clips` joins the five terminal clips (1:53). For the office premium on v14_cells, the last part of `agent_ide` shows the final numbers.
Re-record with `cd part2/video/tapes && vhs clipN.tape` (`head.tape` holds the checkout and Kaggle CLI paths of this machine); the Kaggle
clips read the token from the environment, so it never appears on screen or in a tape.
