# Trust, validation and guardrails

## Roles and review gates (operating model)

Two people, roles by expertise. The actuary (15 years) builds and runs the
harness and signs the actuarial judgments; the data scientist (2 years, no
actuarial background) owns the pipeline and reviews the agent's technical
output. No peer actuary is on the team, so an AI second reader — a session
that did not do the work — reviews the actuarial judgments; the report
states this limitation. Preparer and reviewer are never the same person at
any gate.

| Gate | When | Reviewer | Question |
|---|---|---|---|
| ① Ingest | Agent output (cleaned tables, modelling tables) before it enters `pipeline/` | Data scientist | Implementation correct? Fold design leak-free? Columns, types, joins, offsets as documented? |
| ② Promote | A rule enters a playbook (PR) | Data scientist and actuary, different questions | DS: general, implementable, no conflict with existing rules. Actuary: actuarially right. |
| ③ Release | Before any Kaggle submission | Data scientist (preparer ≠ releaser) | `check_sub` read, level by line reconciled to history, logged with commit hash. |
| ④ Sign | Adaptation decisions, target notes, report | Actuary, with AI second reader's notes | Judgments stated, justified, uncertainty quantified. |

Full procedure: `eval/LOOP.md` Part A.

## Validation
- Local validation is time-ordered (train ≤ Y−1 → predict Y). Random
  K-fold across policy-years is prohibited (same policy spans years).
- A change is adopted only when every available fold moves in the same
  direction by more than the noise floor; single-seed results are never
  decisive (3-seed averages).
- When a validation rule cannot be applied as written (e.g. one fold only
  in the emerging market), the agent must say so, propose the closest
  substitute, and escalate it in the retrospective.
- Common out-of-time test for every (data version, model) pair:
  `holdout_2024.csv` (trained without 2024 emerging rows, predicting every
  2024 training row), graded by `eval/grade_holdout.py` against one fixed
  truth. Data effects are measured with the model frozen (M0); model
  changes are measured on a fixed data version. Public-leaderboard
  differences are read against the estimated noise floor (≈0.0015–0.002
  on the Part 2 public set); differences inside it are reported as not
  measurable.

## Automated checks
- `harness/tools/validate_outputs.py` — all deliverables present, findings
  conform to `harness/schemas/findings.schema.json`, holdout file shape and
  coverage.
- `harness/tools/check_sub.py` — row coverage, uniqueness, non-negativity,
  predicted rate per exposure vs history by line, max prediction.
- `harness/tools/lint_harness.py` — every playbook rule has a registry
  entry and vice versa.
- `tools/check_repo.py` — pre-commit: blocks commits containing data files
  or tokens.

## Agent containment
- The agent works only inside `harness/`: reads outside the folder are
  blocked, `eval/`, `runs/`, `week1_output/`, `week2_data/` are denied
  explicitly, harness files (charter, playbooks, registry, schema,
  templates, tools) are read-only to it, and web, Kaggle, `curl`, `wget`
  and `git push` are denied (`harness/.claude/settings.json`).
- The agent never submits to Kaggle and never promotes a rule. It
  proposes; humans decide and record provenance in
  `harness/memory/registry.yaml`.
- Rules teach method, never market-specific answers (R-0408).

## Submission controls
- Rules §2.2a allow 10 submissions per UTC day (UTC day starts 08:00 SGT);
  the team plans each day's slots in advance and never spends them on
  differences inside the public-score noise.
- Every submission logged in `submissions/log.csv` with the commit hash,
  data version and model version.
- Two final candidates covering the main level hypothesis split; **one**
  is selected as the Final Submission (Rules §2.2b) with the reasoning
  recorded. Part 1's Final Submission counts equally with Part 2's in the
  40% pricing score (Rules §2.4c) — confirm which Part 1 file is selected.

## Data and secrets
- Data (CC BY-NC 4.0) is never committed or redistributed.
- Kaggle token is rotated at the end of the competition.
