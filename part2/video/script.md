# Video material from the modelling track

The team video follows the teammate's six-scene plan (`W2_video_scene_plan.xlsx`, 4:50 in total). This file gives, scene by scene, the
verified numbers and suggested lines from the modelling track, the corrections to items the plan marks as assumed, and the screen
recordings to cut in. Every number is copied from `part2/LOG.md`, `part2/probes.json` or script output.

## Corrections to the scene plan

| scene | item in the plan | what the record shows |
| --- | --- | --- |
| 4 | "The agent never submits" | True for the data harness. In the modelling track the agent submitted with the Kaggle CLI after the team member set the budget for each round; the final selection is made by a person. Say "the harness never submits" or "no file is submitted without a person's go-ahead". |
| 4 | "D-zero is Evan's unaided port" | The port was AI-assisted (the coding agent wrote it). "Unaided" can only mean "without the harness". |
| 4 | "M-zero is a lean three-leaf GBM blend, fixed seeds ... score the 2024 holdout ... every fold moves the same way by more than the noise floor" | That is the Part 1 rule (two time folds). In Part 2 there is no 2024 holdout: the model is a per-peril prior with shrunk levels, compared on the same five folds grouped by customer with a paired bootstrap, and late submissions are kept or dropped by a rule written before the public score returns. |
| 3 | "I marked [N] sentences I could not implement" | The modelling track did not review the harness rule book line by line, so there is no N. Use a different line (below). |
| 2 | level cost "-9 / -6 / -13%", prior estimate "+4 / -3 / flat" | Not from the modelling track. Measured costs of a 15% level error (public D2, probes on v5 = 0.16797): motor new business -0.00244, buildings new business -0.00085, contents new business -0.00035, renewals -0.00043. Evidence before the leaderboard: the developed market's new-business uplift is +8% motor and +13% buildings; emerging training motor new business A/E 1.23 (se 0.15). |
| 7 | "Data quality drives model quality" | On this data the cleaning alone moved the paired CV by +0.00009 (sd 0.00019) and the public score did not rise (v10 0.17247 against v9 0.17303). The supported claim is narrower: "the harness found what our pipeline found, independently, and the cleaned files are what we ship". |
| 5/6 | "3. uncleaned + optimised does not exist" | It exists: v9 (competition files, our pipeline) public 0.17303. The matrix is complete once the teammate's two files are scored. |

## Scene 2, pricing and adaptation (facts to use)

- Ultimate: developed completion curves; the emerging report lags match (motor median 9 days, 90th percentile 44 against 46).
- Trend: none; two emerging years only, and the fire level alone swung from A/E 3.34 (2023) to 1.10 (2024).
- Transferred broker book: 76% of 2025 rows are new business against 12-15% in training; new-business flag in the prior, then cell levels
  measured on the public board and shrunk for sampling noise (sd of log factor 0.05 to 0.32).
- What carried over: rating-factor effects (log correlation of one-way relativities across markets in the report figure). What did not: levels
  (motor 25% lower, bodily injury 0.64, glass 1.28 of the developed model).
- Weather: 22% of the 2025 buildings rows lie above the developed maximum of the wildfire index, where the tree prior is flat; fire takes the
  developed slope (1.66 per unit, from 1,107 developed fires) instead of a slope fitted on 70 emerging fires.

## Scene 3, effective AI use: suggested line for Evan (about 30 words)

"On my side the agent wrote and ran every experiment, and another agent reviewed its code cold. That review found a missing constant in our
leaderboard solver and two tests that could never fail."

## Scene 4, guardrails: suggested line for Evan (about 45 words)

"Our model is a transferred prior with shrunk levels. Every change is compared on the same five folds with a paired bootstrap by customer,
and before each late submission we wrote down the score that would make us drop it. Three changes won in cross-validation and two lost on the
leaderboard. The one that held was knowledge carried from the developed market: its fire slope on the wildfire index."

Numbers behind it: paired CV gains +0.00018, +0.00098, +0.00075 (v9, v10, v11) came out +0.00003, -0.00056, -0.00063 on the public rows;
the fire term +0.00088 in CV, and v12c (fire term with the v9/v10 average) +0.00086 on the public rows against v10.

## Scene 5, results

| | AI-proposed model, not optimised | our pipeline with leaderboard levels |
| --- | --- | --- |
| competition files | teammate's file 4 (to be scored) | v9 0.17303 |
| cleaned files | teammate's file 2 (to be scored) | v10 0.17247 |

Final file: v13_cells 0.17556, first of 33 on 2026-10-29. It averages v9 and v10 (both data versions) with the developed fire slope (v12c,
0.17333) and multiplies seven motor segments by factors measured with disclosed probes and shrunk for noise. In the matrix it sits beside
the right-hand column, not in one cell.

Model-only reference: v4 0.16135 (no leaderboard information). Validation ladder in CV (pooled D2): constant 0.078, emerging-only GBM 0.118,
Part 1 prior as is 0.134, final 0.141; final recipe on the cleaned files 0.1425. Part 1: private 0.13755, rank 8 of 54.

## Screen recordings

Recorded 2026-10-30 with [VHS](https://github.com/charmbracelet/vhs) from the tapes in `tapes/` (real commands, real output, 1920x1080; the
clips are in `deliverables/video_clips/`, not in the repository): `clip1_tests` (scene 4, 14 s), `clip2_rule` (scene 4, the rule commits
before the v13 scores, 28 s), `clip5_code` (scene 2 or 6, the probe solver and its seven factors, 34 s), `clip3_board` (scene 4/5, every
submission with its score, 16 s), `clip4_office` (scene 2, office premium build-up, 20 s), and `all_clips` in that order. Re-record with
`cd part2/video/tapes && vhs clipN.tape` (`head.tape` holds the checkout and Kaggle CLI paths of this machine); the Kaggle clips read the
token from the environment, so it never appears on screen or in a tape.

The list below was the original plan for recording by hand. Record in a terminal with a large font. The Kaggle token must not appear on screen: set it in the shell before recording
(`export KAGGLE_API_TOKEN=...` in a window that is not recorded) and never type it while recording.

1. Scene 4, tests (5 s): `PYTHONPATH=src:part2 .venv/bin/python -m pytest part2/tests -q` ends with "22 passed".
2. Scene 4, the rule before the result (10 s): `part2/LOG.md` open in the editor at "other directions on the cleaned files (v11)", with the
   line "Rule fixed before the score: keep v11 unless its public score is more than 0.0003 below v9's" highlighted.
3. Scene 4/5, the result (10 s): `kaggle competitions submissions iaa-ai-assisted-hackathon-2026-part-2` showing v13_cells 0.17556 at the top,
   v12c 0.17333 and the seven motor probes below it, then v11 0.17184 under v10 0.17247 and v9 0.17303, each with its description (this list
   is also the probe disclosure).
4. Scene 2, optional (5 s): `PYTHONPATH=src:part2 .venv/bin/python part2/office_premium.py work/p2/final.parquet /tmp/office.csv`, the
   build-up table for the 20 reference policies.
