# How AI was used — and how its output was verified

(Skeleton. Filled in as cycles complete. Keep every claim traceable to a
file in `runs/`, `eval/` or `submissions/`.)

## Week 1 (developed market)
Human + AI pair exploration. Every experiment logged with config, seed set
and fold scores (`week1_output/`). Decision principles that emerged:
time-ordered folds, same-direction adoption rule, 3-seed averaging, noise
floors, equal-weight blends. Full narrative: `week1_output/README.md`.

## Week 2 (emerging market)
Week 1 judgment was codified into a harness (`harness/`) and a fresh agent
was run under it on the new market, with the actuary on the loop.

| Cycle | Harness | Kickoff | Agent output | Scorecard | Promoted |
|---|---|---|---|---|---|
| 1 | v1 | `harness/kickoff_prompt.txt` | `runs/cycle_1/` | `eval/scorecards/cycle_1.md` | → v2 |

## Verification of AI output
- Every data-quality finding is reconciled (row counts, totals before/after).
- `harness/tools/validate_outputs.py` — deliverable completeness and schema.
- `harness/tools/check_sub.py` — submission file guardrails.
- Architect scorecard against an answer key the agent never sees (`eval/`).
- Second-reader review (an AI session that did not do the work) before any
  submission candidate is accepted.

## Measured effect of the harness
(To be filled: scorecard comparison across cycles; if run, the bare-harness
control.)

## Provenance of rules
`harness/memory/registry.yaml`: for each rule — origin (Week 1 experiment,
agent retrospective, actuary), evidence, approver, cycle.
