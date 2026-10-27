# The loop (architect side — never shown to the agent)

The agent's working directory is `../harness/`. Nothing in `eval/`, `runs/`,
`week1_output/` or `week2_data/` is part of its world. The harness is what
the agent inherits; the agent itself keeps no memory between cycles.

This file has two parts. **Part A is the operating model** — how an actuary
and a data scientist run an AI agent on pricing work, in a form that
transfers to practice. **Part B is the measurement design** — what we added
on top, for this competition only, to measure whether the harness helps.
Keep the two apart in the report: the measurement devices (control run,
answer key, code-graded holdout) do not exist in practice; the review
gates do.

---

## Part A — Operating model (transfers to practice)

Two people, roles by expertise, not symmetric.

| Role | Who | Does |
|---|---|---|
| Architect / operator | Actuary (HS, 15 yrs) | Builds and maintains the harness; runs each cycle; extracts promotion candidates from the retrospective; makes and **signs the actuarial judgments** (adaptation decisions, borrowed IBNR tail, trend, line levels, office premium, uncertainty statements). |
| Technical reviewer | Actuarial data scientist (Evan; formerly in the same actuarial department) | Owns the modelling pipeline and the prediction files. Reviews the agent's **technical** output at three gates (below). Reads the playbooks as their intended real-world reader. |
| AI second reader | A separate AI session that did not do the work | Reviews the actuarial judgments the actuary signs, because no peer actuary is on the team. The report says so plainly: in practice this seat is a peer actuary. |

### Review gates

| Gate | When | Reviewer | Question asked |
|---|---|---|---|
| ① Ingest | Before any agent output (cleaned tables, modelling tables) enters `pipeline/` | Evan | Is the implementation correct? Leakage in the fold design? Columns, types, joins, completion offsets as documented? |
| ② Promote | Before a rule enters a playbook (PR) | Evan **and** HS, different questions | Evan: is it general (would it apply to data we have never seen), implementable, free of conflict with existing rules? HS: is it actuarially right? |
| ③ Release | Before any Kaggle submission | Evan (preparer ≠ releaser) | `check_sub` read; level reconciliation by line explained; logged with commit hash in `submissions/log.csv`. |
| ④ Sign | Before adaptation decisions, target notes or the report are final | HS, with the AI second reader's notes attached | Are the judgments stated, justified, and their uncertainty quantified? |

**Playbook usability read (once, ~30 min, Evan).** Read every playbook as a
colleague who must implement it and mark each sentence that is unclear
or not implementable. This is the test of whether the harness carries the
actuary's judgment to its real reader; the marked sentences are rewritten
(method clarified, never answers added) and the count goes in the report.

### Per cycle

1. **Prepare** (HS)
   - Run from an isolated copy outside the repository
     (`C:\Users\Guest1337\harness_run`): copy `harness/` minus `memory/`,
     `outputs/`, `work/`; the copy has no git context above it and no
     `../eval` to reach. Isolation is physical, so the settings file runs
     with `bypassPermissions` and without the read block (the read block
     prompts on every stdin-code command and stalls an unattended run).
   - `data/emerging/` and `data/developed/` hold a copy of the competition
     data (read-only to the agent; gitignored).
   - Empty `harness/outputs/` and `harness/work/`. Keep `CLAUDE.md`,
     `playbooks/`, `templates/`, `schemas/`, `tools/`, `memory/`.
   - Confirm no `CLAUDE.md` / `AGENTS.md` exists in any parent folder of
     `harness/`, and that your global Claude Code user instructions are
     empty or irrelevant.
   - Record the harness tag (`harness-vN`) the cycle runs on.

2. **Run** (HS)
   - Open a NEW Claude Code session with `harness/` as the working
     directory (fresh conversation, nothing continued).
   - Paste `harness/kickoff_prompt.txt` verbatim as the first and only
     message. Note start time.
   - On the loop, not in it: no hints, no follow-ups. If the agent asks a
     question, answer only "Decide and record your rationale." Note
     anything you had to approve or refuse.
   - Note end time and the session's token/cost figure if shown.

3. **Collect** (HS)
   - Copy `harness/outputs/*` to `runs/cycle_N/` (findings.json, the
     markdown deliverables, baseline/ if present; `cleaned/` and
     `modelling_tables/` are not committed — derived from CC BY-NC data —
     keep their row counts in the scorecard).
   - Save the session log to `runs/cycle_N/log.md`: times, interventions,
     cost, anything refused.

4. **Review** (gates ① and ④)
   - Evan: gate ① on the cleaned tables and modelling tables before they
     go to `pipeline/` as data version **D_k** (see Part B).
   - HS: read `adaptation_decisions.md`, `target_notes.md` and the
     `team_query` items; decide each; record decisions in
     `runs/cycle_N/decisions.md`. Attach the AI second reader's notes.

5. **Promote** (gate ②) — the only thing that changes between cycles
   - Read `retrospective.md` → "Proposed additions" and "Rules I could not
     apply as written". For each candidate: accept / rewrite-to-generalise /
     reject. Admissible only if it would be sensible advice for a market
     whose issues you had never seen. Teach method, never location, never
     counts.
   - Add your own rules from the review, tagged ACTUARY.
   - Open a PR: new rules appended to the relevant playbook with the anchor
     `<!-- rule: R-#### -->` and a registry entry (origin, evidence, cycle,
     approver). Evan approves generality/implementability; HS approves
     actuarial content. Never edit `CLAUDE.md` unless a practice is durable
     and universal.
   - Merge; `git tag harness-v(N+1)`.

6. **Next cycle** → step 1.

---

## Part B — Measurement design (this competition only)

Thesis under test: **data quality drives model quality, and a harness that
catches the easy defects frees the agent to find the hard ones.** So the
unit of measurement is a *data version*, not a model.

### Data-version track

| Version | What it is | Produced by | Role |
|---|---|---|---|
| **D0** | The data scientist's own port of the Week 1 preparation to the emerging market, unaided by the harness | Evan | Control: what a competent DS does without the harness |
| **D1** | Modelling tables from Cycle 1 (harness-v1), after gate ① | HS (agent) | First harness version |
| **D2, D3 …** | Modelling tables from Cycle k (harness-vk), each from a fresh agent on the raw data, after gate ① | HS (agent) | Accumulated promotions |

A data version is the set `modelling_tables/{motor,buildings,contents}.parquet`
(cleaned rows **and** target, completion, exclusions, mapped features) plus
`adaptation_decisions.md`. Row-level repairs alone barely move the score;
target construction and leakage exclusions do (Part 1: host GLM without IBNR
treatment 0.109 vs first submission 0.127). The agent retains nothing between
cycles; the harness retains what was approved, so D_k improves only through
promoted rules.

### Measuring instrument: a frozen model

- **M0** is fixed after D0 (lean 3-leaf GBM blend, fixed seeds, fixed config).
  Every data version is trained with M0 unchanged; the difference between
  D_k×M0 and D_{k−1}×M0 is the data effect.
- Model improvements run on a separate **model track** on a fixed data
  version (M1, M2 … on the latest converged D_k), adopted under R-0202.
- Every submission is logged with both coordinates (`data_version`,
  `model_version`) in `submissions/log.csv`; the report shows the matrix.

### Agent-built baselines are not the instrument
Fresh agents make different single-fold modelling choices (cycle 1: 300
rounds; cycle 2: 75 rounds and an explicit level factor) and their holdout
scores move accordingly (0.1125 → 0.0978) while the data versions they
produced were identical. The agent's stretch baseline is evidence about the
*modelling playbook*, never about the data; the data effect is read only
from the frozen pipeline model M0.

### Three layers of grading

| Layer | What | Who | Catches |
|---|---|---|---|
| ① Scorecard vs answer key | Per cycle: detection, treatment, false alarms, decision table, uncertainty (`scorecard_template.md`), **and** for every finding whether a rule led to it (`triggered_by_rules` non-empty = rule-caught; empty = novel) | Sections A, D (technical) → Evan; B, C, E (actuarial) → HS + AI second reader | What the leaderboard cannot see; the resource thesis |
| ② Code-graded holdout | `holdout_2024.csv` for each (D_k, M) — trained without 2024 emerging rows — scored by `eval/grade_holdout.py` against one fixed truth | code | Noise-controlled data effect; zero submission slots |
| ③ Public leaderboard | D_k×M0 once per data version; model-track candidates | Evan releases (gate ③) | External confirmation, read against the noise floor (≈0.0015–0.002 on ≈69k public rows; Part 1: 0.0009 on ≈207k). Inside the band = "not measurable" |

### The headline figure

One chart per cycle: stacked bars of findings **rule-caught / novel / missed
(vs answer key)**, with the holdout D² of D_k×M0 as a line. The thesis
predicts: rule-caught rises as novel findings of cycle k become rules of
cycle k+1; novel findings appear earlier in the run (time to first novel
finding from the session log); D² rises then flattens.

### Convergence and stopping

Stop the data track when a cycle produces no novel finding **and** the
holdout ΔD² of D_k×M0 vs D_{k−1}×M0 is inside the noise floor. Expect this
after two or three cycles — the defect list is finite. Record it as a result
("data quality converged at D_k"); later cycles are justified only by
sharper adaptation decisions and uncertainty statements, which the scorecard
sections B and E measure.

### Optional control: Arm 0
`eval/cycle0_bare/` + `eval/make_cycle0.py` build a workspace with the same
charter, templates, schema and tools but no playbooks. It isolates the
playbooks' contribution from the charter's. Run it only if time allows
(operator must not have read `answer_key.md`); D0 already serves as the
practical control.

### Integrity rules for the architect
- Harness v1 contains ONLY rules traceable to the Week 1 README plus the
  Part 2 adaptation protocol (actuary-authored method). Nothing learned
  from the architect's own profiling of the emerging data enters the
  harness until the agent has had its chance to find it (Cycle 1).
- When reviewing, distinguish "what I already knew" (answer key) from
  "what the agent found"; the registry `origin` field records which.
- The holdout truth (`grade_holdout.py`) is built from raw data with the
  minimum treatment that does not depend on any judgment call (claim–row
  linkage by loss date, net incurred, repudiated = 0). It is not the
  cleaned data of any version.
- The answer key is the architect's independent profile, written before any
  agent run. In practice there is no answer key; the reviewer's spot checks
  and the reconciliation rules (R-0012, R-0208) stand in its place — say so
  in the report.
