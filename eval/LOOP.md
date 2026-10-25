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
   - `harness/data/emerging/` and `harness/data/developed/` hold a copy of
     the competition data (read-only to the agent; gitignored).
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
     go to `pipeline/`.
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

Purpose: say with evidence whether Week 1 knowledge, delivered as a
harness, changed what the agent did on the new market. Three arms:

| Arm | What | Operated by | Exists in practice? |
|---|---|---|---|
| **A** | Human DS + AI pair port of the Part 1 blend, level re-estimated | Evan | yes — this is ordinary modelling work |
| **B** | Agent under harness-vN (Cycle N), including its stretch baseline | HS | yes — the operating model above |
| **0** | Agent under the same charter, templates, schema and tools, **no playbooks, no registry** (`eval/cycle0_bare/`) | Evan (near-idle: paste kickoff, do not intervene, collect) | **no** — control arm |

Arm 0 vs B measures the playbooks' contribution (the charter, templates and
deliverable structure are held constant, so this is a lower bound on the
whole harness's effect). A vs B decides the final blend and is reported as
"human-led vs agent-led under harness".

Integrity: Evan operates Arm 0 **before** reading `answer_key.md`; neither
operator intervenes in a run; the kickoff prompt is identical.

### Three layers of grading

| Layer | What | Who | Catches |
|---|---|---|---|
| ① Scorecard vs answer key | Detection, treatment, false alarms, decision table, uncertainty, deliverable completeness (`scorecard_template.md`) | **Split by expertise**: items A, D (technical, objective) → Evan; items B, C, E (actuarial judgment) → HS + AI second reader. Each grades both arms on their items. | The 60% of judging the leaderboard cannot see |
| ② Code-graded holdout | Each arm's `outputs/baseline/holdout_2024.csv` (2023-only training → 2024 rows) scored by `eval/grade_holdout.py` against the architect's 2024 target | code | Noise-controlled accuracy, same truth for every arm, zero submission slots |
| ③ Public leaderboard | One submission per arm | Evan releases (gate ③) | External confirmation. Report with the noise floor: Part 1 pairwise noise was ≈0.0009 on ≈207k public rows; Part 2 public set is ≈69k rows → expect ≈0.0015–0.002. A difference inside that band is reported as "not measurable". |

The answer key is the architect's independent profile, written before any
agent run. In practice there is no answer key; the reviewer's spot checks
and the reconciliation rules (R-0012, R-0208) stand in its place — say so
in the report.

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
  cleaned data of any arm.
