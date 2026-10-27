# How AI was used — and how its output was verified

(Skeleton. Filled in as cycles complete. Every claim must be traceable to a
file in `runs/`, `eval/` or `submissions/`.)

## Week 1 (developed market)
Human + AI pair exploration by the data scientist. Every experiment logged
with config, seed set and fold scores (`week1_output/`). Decision
principles that emerged: time-ordered folds, same-direction adoption rule,
3-seed averaging, noise floors, equal-weight blends. Full narrative:
`week1_output/README.md`.

## Week 2 (emerging market) — data-version track

Thesis: data quality drives model quality; a harness that catches the easy
defects frees the agent for the hard ones. The unit of measurement is a data
version, trained with one frozen model.

| Version | What | Produced by | AI's role | Verification |
|---|---|---|---|---|
| D0 | Week 1 preparation ported to the emerging market, unaided | Data scientist | Pair programming, as in Week 1 | Fold scores, `check_sub`, holdout grading |
| D1, D2 … | Modelling tables from harness cycle k (`harness-vk`), fresh agent each time | Actuary (operator) | Autonomous end-to-end: profiling, cleaning, shift report, targets, adaptation decisions | `validate_outputs`, reconciliations, gate ① technical review, gate ④ actuarial sign-off, scorecard vs answer key, holdout grading |
| M0 | Frozen lean 3-leaf GBM blend, fixed seeds — the measuring instrument | Data scientist | — | Unchanged across D_k |
| M1 … | Model-track changes on the latest converged D_k | Data scientist | Pair programming | R-0202, holdout, leaderboard with noise floor |

The harness is the actuary's judgment written down so that a fresh agent —
and a colleague — can execute it. Its real-world reader is the
data scientist, who reads every playbook once and marks sentences that are
unclear or not implementable; the count and the fixes are reported.

Each operator documents their own AI use: the actuary in `runs/` and this
file; the data scientist in `pipeline/README.md` (which prompts, which
checks, what was rejected and why).

## Cycle log

| Cycle | Harness (rules) | Fresh? | Wall / API | Cost | Findings rule-caught / novel / missed | Agent-baseline holdout D² | Data version vs previous | Promoted |
|---|---|---|---|---|---|---|---|---|
| 1 | v1 (50) | yes | 75 min / 45 min | $20.93 | 15 / 8 / 0 | 0.1125 | D1 (first) | 13 rules → v2 |
| 2 | v2 (63) | **no** — read cycle 1's auto-memory note (disclosed in scorecard) | 4h17 incl. hand-approved prompts and one restart / 53 min | $25.71 | 17 / 6 / 0 | 0.0978 | D2 = D1 (rows, exposure, Σy identical) | 10 proposals → v3 |
| 3 | v3 (67) | yes (fresh folder) | 44 min / 41 min | $19.09 | 23 / 2 / 0 | 0.1065 | D3 = D2 = D1 | 8 proposals → v4 |
| 4 | v4 (68) | yes (fresh folder) | 59 min / 42 min | $22.29 | 23 / 2 / 0 (both trivial) | 0.1031 | D4 = D3 on targets; nulls reduced by sibling reconstruction | v5 = final recorded state |

Effort was constant across cycles (API time 45 / 53 / 41 / 42 min; output tokens 192k / 210k / 187k / 184k; cost $21 / $26 / $19 / $22); wall-clock includes operator response time and is not a measure of the agent. Answer key: 10 items, all found in every cycle; the agent found two defects the key missed in cycle 1 and three more structural facts in cycles 2–3 (survivor-sample first year, non-terminating "declined" label, zero-length rows). Agent-built baselines vary with single-fold modelling choices and are not the measure of data quality (LOOP.md); the data effect is read from the frozen pipeline model.

Floor for the holdout: a constant 2023 burning cost by line scores D² 0.068
(`eval/holdout_results.csv`, `naive_2023_rate`). Data track stops when a
cycle finds nothing novel and the holdout gain is inside the noise floor.

## Verification of AI output
- Every data-quality finding is reconciled (row counts, totals before/after).
- `harness/tools/validate_outputs.py` — deliverable completeness, schema,
  holdout coverage.
- `harness/tools/check_sub.py` — submission file guardrails.
- Architect scorecard against an answer key the agent never sees (`eval/`),
  with technical items graded by the data scientist and actuarial items by
  the actuary plus an AI second reader.
- Code-graded out-of-time test (`eval/grade_holdout.py`), one truth for all
  arms.

## Provenance of rules
`harness/memory/registry.yaml`: for each rule — origin (Week 1 team
learning, agent retrospective, actuary), evidence, approver, cycle. Counts
by origin are reported per harness version.
