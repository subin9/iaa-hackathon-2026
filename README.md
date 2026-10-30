# IAA AI-Assisted Actuarial Hackathon 2026: team SU² (Kaggle team HS)

Risk premium models for three lines of personal insurance (private motor, home buildings, home contents), first for a developed market
(Part 1) and then for an emerging market the insurer expands into (Part 2). The score is the Tweedie D² with power 1.5 on the expected
ultimate claim cost of every 2025 policy row.

- Part 1: https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1
- Part 2: https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2

## Results

| | final submission | public | private | notes |
| --- | --- | --- | --- | --- |
| Part 1, developed market | `eq20` | 0.12956 | 0.13755 (rank 8 of 54) | equal-weight blend of shallow GBMs, GLM, EBM, MLP, CatBoost, TabM; credibility factor; levels from the public board |
| Part 2, emerging market | `v13_cells` | 0.17556 (first of 38 on 2026-10-30) | after close | transferred per-peril prior on the cleaned files, shrunk peril levels, screened corrections, developed-market fire slope, cell and motor segment levels from the public board |

Each late version replaced the previous one only under a rule written in `part2/LOG.md` before its score came back: `v12c` (0.17333, the
`v9`/`v10` average with the fire term) replaced `v10` (0.17247), and `v13_cells` (`v12c` times seven shrunk motor segment factors) replaced
`v12c`. The reasoning is in section 7 of the report. Without any leaderboard information the Part 2 model scored 0.16135 (`v4`); most of the
rest comes from levels measured with disclosed leaderboard probes.

## Deliverables in this repository

| what | where |
| --- | --- |
| Written report (5 pages) | `part2/report/out/report.pdf`, built by `part2/report/build_report.py` |
| Video material | `part2/video/` (script, slides, notes for the screen recordings) |
| Part 1 development log | `docs/part1_log.md`, public scores in `docs/part1_public_scores.csv` |
| Part 2 working log | `part2/LOG.md` (every experiment, its numbers and the decision taken) |
| Part 2 leaderboard record | `part2/probes.json` (every submission and probe with its public score) |
| How AI was used and checked | `docs/AI_USAGE.md` |
| Final choice | `part2/final.json` |

The prediction files themselves are submitted on Kaggle and through the final submission form. They are not stored here because they
are keyed by the competition's row identifiers.

## Layout

```
src/            Part 1 code: data preparation (prep.py), model runners (run.py, cb.py, ebm.py, nn.py, tabm_run.py, tabm_peril.py, ag.py, glm.py, fs.py),
                blend and submission (make_sub.py, transfer.py, level_probe.py, check_sub.py), experiment harnesses (exp.py, exp2.py)
eda/            Part 1 exploration scripts
part2/          Part 2 pipeline, experiments e0 to e25, probes, tests, report and video (see part2/README.md)
docs/           Part 1 log, AI use
pyproject.toml, uv.lock     main environment (uv); groups "report" (weasyprint, matplotlib) and "dev" (pytest)
requirements-ag.txt         second environment for AutoGluon, CatBoost, EBM and TabM (Part 1 only)
```

## Set-up

1. Python 3.12 and [uv](https://docs.astral.sh/uv/). `uv sync --group report --group dev` creates `.venv`.
2. Part 1 models that need AutoGluon, CatBoost, EBM or TabM run in a second environment:
   `uv venv .venv-ag && uv pip install --python .venv-ag/bin/python -r requirements-ag.txt`.
3. Data (not in the repository, see below):
   - Part 1 download in `data/public/*.parquet`
   - Part 2 download in `data/part2/developed/` and `data/part2/emerging/`
   - the teammate's cleaned emerging files (`IAA_AI_Hackathon_week2_cleaned.zip`) unzipped to `data/part2_cleaned/`
4. Every command runs from the repository root, for example `PYTHONPATH=src:part2 .venv/bin/python part2/fit_final.py ...`.
   Long jobs were run with 8 threads and a memory cap (16 cores, 30 GB RAM).

## Reproduce

- Part 2, all submitted versions: `bash part2/run_all.sh` (about 40 minutes on 8 cores). It rebuilds the tables, the developed-market priors,
  the tests, every version from v4 to v13 and the office premium table. `v7` and `v11` rebuild byte for byte; `v10` rebuilds to a largest row difference of 3e-13 (floating-point order),
  `v12c` and `v13_cells` to 1e-14 (relative).
- Part 1, `eq20`: the command chain is in `docs/part1_log.md`, section "Reproducing the final Part 1 submission".
- Tests: `PYTHONPATH=src:part2 .venv/bin/python -m pytest part2/tests -q` (22 tests, a few seconds).
- Report and slides: `part2/report/figures.py`, `part2/report/build_report.py`, `part2/video/slides.py`.

Git tags mark the code behind the main submitted files: `p1-eq20` (Part 1 final), `p2-v7`, `p2-v9`, `p2-v10`, `p2-v11`, `p2-v13` (Part 2 final, with `v12c`).
`final-submission` marks the state of the repository handed in with the deliverables.

## Data, credentials and rules

- Competition data stays out of the repository (rules section 2.5): `data/`, `work/`, `submissions/` and `*.zip` are ignored, and the
  history was checked for data files and credentials before the repository was published.
- The Kaggle API token was passed per command as an environment variable and is not in any file or commit.
- Every leaderboard probe is disclosed in `part2/probes.json` and in the report.
- If the team wins, the code is licensed to the sponsor under an open-source licence as rule 2.6 requires.
