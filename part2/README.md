# Part 2: emerging market

Task: expected ultimate claim cost for every 2025 row of the emerging market (motor, buildings, contents), scored with the Tweedie D2 (power 1.5).
Idea: keep the developed-market relativities, re-learn the levels on two emerging years, add only the corrections the data can prove, measure the
new-business levels on the public leaderboard (disclosed) and shrink them for sampling noise. Everything is logged in `LOG.md`; the report is built by
`report/build_report.py`, the video material is in `video/` (script, slides, VHS tapes for the screen recordings), the final choice is in `final.json`.

| step | script |
| --- | --- |
| EDA | `eda_01_overview.py`, `eda_02_quality.py`, `eda_03_missing_drift.py`, `eda_04_drift.py`, `eda_05_oneway.py`, `eda_06_weather.py` |
| tables | `prep_emerging.py` (emerging), `harmonize.py` (developed tables on the emerging coding; needs `work/{line}.parquet` from `src/prep.py`) |
| prior | `devprior_peril.py` (per-peril developed model, variants by env), `average_priors.py`, `devprior.py` (line-level prior, early experiments) |
| model | `model2.py` (levels, corrections), `adapt.py` (robust score test + ridge Tweedie GLM), `lib.py` (shared helpers) |
| experiments | `e0` zero-shot, `e1` emerging-only, `e2` transfer, `e3` residuals, `e4` corrections, `e5` to `e9` peril levels, `e10` pipeline CV, `e11` vehicle details, `e12` experience rating, `e13` sampling noise of a probed factor, `e14` emerging-only blend, `e15` weather out of time, `e16` private carry-over, `e17` prior variants, `e18` peril levels, `e19` cap and excess, `e20` paired bootstrap, `e21` cleaned files, `e22` second round on them, `e23` residual boosting, `e24` joint prior, `e25` weather on single perils |
| submission | `fit_final.py` (fit and score), `probe.py` (segment probe files), `probe_solve.py`, `probe_solve_struct.py`, `probe_solve_ridge.py`, `probe_solve_cells.py` (solve levels from probes), `shrink_multipliers.py`, `transplant_cells.py` (carry the cell levels to a new base), `residual_motor.py` (v11), `fire_term.py` and `geo_mean.py` (v12c), `probe_q12.py` and `probe_overlays.py` (motor segment probes, v13), `submission.py` (format checks), `office_premium.py` |
| checks | `tests/test_part2.py` (22 tests), `report_numbers.py` (validation ladder) |
| record | `LOG.md`, `probes.json` (every submission and probe with its public score), `v5_args.txt`, `v5_probes.json`, `q12_probes.json`, `final.json` |

Versions (public D2): v0 0.14872, v1 0.15483, v2 0.15938, v3_half 0.16446, v4 0.16135, v5_full 0.16797, v6 0.17182, v7 0.17300, v9 0.17303,
v10 0.17247, v11 0.17184, v12c 0.17333, v13_raw 0.17552, v13_cells 0.17556 (final). v0 to v4 use no leaderboard information.

Run order: `run_all.sh`. Environment: `uv sync --group report --group dev`; commands run from the repo root with `PYTHONPATH=src:part2`. Variables: `P2_TAG`
(prior file suffix), `P2_KEEP` (columns kept despite the drop lists), `P2_DROP` (columns left out), `P2_VARIANT` (poisson or extra), `P2_POWER`, `P2_ONLY` (one line).
Data (`data/part2`, `data/part2_cleaned`) is the competition download and the teammate's cleaned copy, and is not part of the repository.
