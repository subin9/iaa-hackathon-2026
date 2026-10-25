# How AI was used — and how its output was verified

(Skeleton. Filled in as cycles complete. Every claim must be traceable to a
file in `runs/`, `eval/` or `submissions/`.)

## Week 1 (developed market)
Human + AI pair exploration by the data scientist. Every experiment logged
with config, seed set and fold scores (`week1_output/`). Decision
principles that emerged: time-ordered folds, same-direction adoption rule,
3-seed averaging, noise floors, equal-weight blends. Full narrative:
`week1_output/README.md`.

## Week 2 (emerging market) — three arms

| Arm | What | Operated by | AI's role | Verification |
|---|---|---|---|---|
| A | Part 1 blend ported, levels re-estimated | Data scientist | Pair programming and analysis, as in Week 1 | Fold scores, `check_sub`, holdout grading, gate ③ |
| B | Fresh agent under the harness (`harness/`, tag `harness-vN`) | Actuary | Autonomous end-to-end: profiling, cleaning, shift report, targets, adaptation decisions, baseline | Self-checks (`validate_outputs`), reconciliations, gate ① technical review, gate ④ actuarial sign-off, scorecard vs answer key, holdout grading |
| 0 | Same agent, same charter and templates, **no playbooks** (`eval/cycle0_bare/`) | Data scientist | Control: what the agent does without Week 1 knowledge | Same scorecard and holdout grading as B |

The harness is the actuary's judgment written down so that a fresh agent —
and a colleague — can execute it. Its real-world reader is the
data scientist, who reads every playbook once and marks sentences that are
unclear or not implementable; the count and the fixes are reported.

Each arm's operator documents their own AI use: the actuary in `runs/` and
this file; the data scientist in `pipeline/README.md` (which prompts, which
checks, what was rejected and why).

## Cycle log

| Cycle | Arm | Harness | Kickoff | Output | Scorecard | Holdout D² | Promoted |
|---|---|---|---|---|---|---|---|
| 0 | 0 | charter only | `harness/kickoff_prompt.txt` | `runs/cycle_0/` | `eval/scorecards/cycle_0.md` | `eval/holdout_results.csv` | — |
| 1 | B | v1 (50 rules) | same | `runs/cycle_1/` | `eval/scorecards/cycle_1.md` | same | → v2 |

Floor for the holdout: a constant 2023 burning cost by line scores D² 0.068
(`eval/holdout_results.csv`, `naive_2023_rate`).

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
