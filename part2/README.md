# Part 2: emerging market

Task: expected ultimate claim cost for every 2025 row of the emerging market (motor, buildings, contents), scored with the Tweedie D2 (power 1.5).
Idea: keep the developed-market relativities, re-learn the levels on two emerging years, add only the corrections the data can prove, calibrate the new-business level
on the public leaderboard. Everything is logged in `LOG.md`; the report is built by `report/build_report.py`, the video material is in `video/`.

| step | script |
| --- | --- |
| EDA | `eda_01_overview.py`, `eda_02_quality.py`, `eda_03_missing_drift.py`, `eda_04_drift.py`, `eda_05_oneway.py`, `eda_06_weather.py` |
| tables | `prep_emerging.py` (emerging), `harmonize.py` (developed tables on the emerging coding; needs `work/{line}.parquet` from `src/prep.py`) |
| prior | `devprior_peril.py` (per-peril developed model, variants by env), `average_priors.py`, `devprior.py` (line-level prior, used by early experiments) |
| model | `model2.py` (levels, corrections), `adapt.py` (robust score test + ridge Tweedie GLM) |
| experiments | `e0` zero-shot, `e1` emerging-only, `e2` transfer, `e3` residuals, `e4` corrections, `e5` to `e9` peril levels, `e10` pipeline CV, `e11` vehicle details, `e12` experience rating |
| submission | `fit_final.py` (fit and score), `probe.py` (segment multipliers), `probe_solve.py` (solve the best multipliers from probes), `submission.py` (format checks), `office_premium.py` |
| checks | `tests/test_part2.py` (22 tests), `report_numbers.py` (validation ladder) |

Run order: `run_all.sh`. Environment: `uv sync`; commands run from the repo root with `PYTHONPATH=src:part2`. Variables: `P2_TAG` (prior file suffix), `P2_KEEP` (lean columns kept),
`P2_DROP` (columns left out), `P2_VARIANT` (poisson or extra), `P2_ONLY` (one line). Data (`data/part2`) is the competition download and is not part of the repository.
