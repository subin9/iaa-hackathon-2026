# IAA AI Assisted Hackathon 2026 — Team repository

Two-person team: an actuary (harness, validation, governance, report) and a
data scientist (modelling pipeline). This README is organised by the four
judging criteria so that a reader — human or AI screening tool — can find
the evidence for each.

## 1. Pricing performance & adaptation (40%)
- Part 1 (developed market): see `week1_output/README.md` — the full
  experiment log, what worked, what did not, final blend (eq20).
- Part 2 (emerging market): data versions D0 (data scientist's own port)
  and D1, D2 … (harness cycles, `runs/cycle_N/`) trained with one frozen
  model M0, then a model track on the converged data (`pipeline/`). The
  per-component carry-over decisions are in
  `runs/cycle_N/adaptation_decisions.md`; remaining uncertainties are
  stated there and in `report/`. Design: `eval/LOOP.md`.

## 2. Effective use of AI (25%)
- `AI_USAGE.md` — where AI was used, how its outputs were verified, and the
  measured effect of the harness.
- `harness/` — the operating environment handed to a fresh AI agent: charter
  (`CLAUDE.md`), method-only playbooks distilled from Week 1, templates,
  self-check tools. `harness/memory/registry.yaml` records the origin,
  evidence and approver of every rule.
- `eval/` — architect-side loop (`LOOP.md`: operating model and
  measurement design), answer key, scorecards, control-arm charter
  (`cycle0_bare/`), code-graded holdout (`grade_holdout.py`). Never
  visible to the agent.

## 3. Trust, validation & guardrails (20%)
- `GUARDRAILS.md` — roles and four review gates (actuary signs judgments,
  data scientist reviews implementation and releases), validation rules,
  automated tests, agent containment, submission controls.
- `harness/tools/` — `validate_outputs.py`, `check_sub.py`.
- `tools/check_repo.py` — pre-commit guard: no data, no tokens.

## 4. Communication & documentation (15%)
- `report/` — the 5-page write-up; `video/` — link to the 5-minute demo.
- `submissions/log.csv` — every Kaggle submission with commit hash and score.
- Git history: tags `harness-vN` mark each promotion of the harness,
  `sub-w2-NNN` each submission, `final-submission` the graded state.

## Reproduce
Data is not in this repository (CC BY-NC 4.0). Download both folders from the
Part 2 competition page into `harness/data/{developed,emerging}/` (agent runs)
and `pipeline/data/` (modelling pipeline). Then see `harness/CLAUDE.md` and
`pipeline/README.md`.
