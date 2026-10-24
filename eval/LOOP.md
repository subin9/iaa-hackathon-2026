# The loop (architect side — never shown to the agent)

The agent's working directory is `../harness/`. Nothing in `eval/`, `runs/`,
`week1_output/` or `week2_data/` is part of its world. The harness is what
the agent inherits; the agent itself keeps no memory between cycles.

## Per cycle

1. **Prepare**
   - `harness/data/emerging/` and `harness/data/developed/` hold a copy of
     the competition data (read-only to the agent; gitignored).
   - Empty `harness/outputs/` and `harness/work/`. Keep `CLAUDE.md`,
     `playbooks/`, `templates/`, `schemas/`, `tools/`, `memory/`.
   - Confirm no `CLAUDE.md` / `AGENTS.md` exists in any parent folder of
     `harness/`, and that your global Claude Code user instructions are
     empty or irrelevant.
   - Record the harness tag (`harness-vN`) the cycle runs on.

2. **Run**
   - Open a NEW Claude Code session with `harness/` as the working
     directory (fresh conversation, nothing continued).
   - Paste `harness/kickoff_prompt.txt` verbatim as the first and only
     message. Note start time.
   - On the loop, not in it: no hints, no follow-ups. If the agent asks a
     question, answer only "Decide and record your rationale." Note
     anything you had to approve or refuse.
   - Note end time and the session's token/cost figure if shown.

3. **Collect**
   - Copy `harness/outputs/*` to `runs/cycle_N/` (findings.json,
     cleaned/ excluded — too large and derived from CC BY-NC data;
     keep row counts in the scorecard instead).
   - Save the session transcript or its summary to `runs/cycle_N/log.md`
     (times, interventions, cost).

4. **Score**
   - Fill `eval/scorecards/cycle_N.md` from `scorecard_template.md`
     against `answer_key.md`: detection, treatment, false alarms,
     adaptation decisions, handling of rules that could not be applied,
     deliverable completeness, time, cost.
   - Optionally a second-reader AI review in a SEPARATE folder (so the
     analyst CLAUDE.md is not loaded): give it outputs + scorecard, ask for
     disagreements and missed items. Record its view in the scorecard.

5. **Promote** (the only thing that changes between cycles)
   - Read `retrospective.md` → "Proposed additions". For each candidate:
     accept / rewrite-to-generalise / reject. Admissible only if it would
     be sensible advice for a market whose issues you had never seen.
     Teach method, never location, never counts.
   - Add your own rules from the scorecard review, tagged ACTUARY.
   - Append accepted rules to the relevant playbook with the anchor
     `<!-- rule: R-#### -->` and add the registry entry with origin,
     evidence, cycle, approver. Never edit `CLAUDE.md` unless a practice
     is durable and universal.
   - `git tag harness-v(N+1)`.

6. **Next cycle** → step 1.

## Controls (optional, if time allows)
- **Cycle 0 (bare):** same kickoff, `CLAUDE.md` with deliverables only, no
  playbooks, no templates. Score with the same scorecard. The difference
  to Cycle 1 is the measured contribution of Week 1 knowledge.

## Integrity rules for the architect
- Harness v1 contains ONLY rules traceable to the Week 1 README plus the
  Part 2 adaptation protocol (actuary-authored method). Nothing learned
  from the architect's own profiling of the emerging data enters the
  harness until the agent has had its chance to find it (Cycle 1).
- When reviewing, distinguish "what I already knew" (answer key) from
  "what the agent found"; the registry `origin` field records which.
