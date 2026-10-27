# Scorecard — cycle 2 (harness-v2 → data version D2)

Run: 2026-10-27 ≈11:30 → 15:28 SGT (two restarts for permission-mode changes, no content instruction) | operator: HS | model: claude-fable-5-1, xhigh | location: isolated copy, memory/ removed | cost: … (from `/cost`)

## A. Detection and treatment — technical (draft, Evan to confirm)
23 findings: **rule-caught 17 · novel 6 · missed 0** (cycle 1: 15 / 8 / 0). What was novel in cycle 1 is now rule-caught: 360-day exposure (R-0014), ×1000 by ratio (R-0013), pre-inception claims by lag (R-0015), campaign_code cohort stamp (R-0016), flood_zone MNAR and the 12% MCAR block (R-0018), missing comparison-site commission (R-0412). All ten answer-key items found again with the same treatments and counts.

New this cycle (novel, verified): **F-SURVIVOR-2023** — 100% of 2023 policies reappear in 2024 and no 2023 row is lapsed or cancelled, so the first training year is a survivor sample (true for the developed 2021 year as well: 100% persistence — a Part 1 fact nobody recorded). **F-AGEBAND-CONFLICT** — age band disagrees between lines for 0.3% of customer-years. Also F-GENDER raised as a regulatory finding.

False alarms: none confirmed.

## B/C/E — actuarial (HS)
- Completion: anchor moved to 12 months with the empirical 12-vs-24-month check on the oldest year (new, proposal 7) — ☐ HS to compare with cycle 1's 18-month anchor.
- Rules not applied: same table as cycle 1, now including R-0312 edge rule.
- Weakest calls: 7 listed; #4 (explicit level factor) and #5 (marketing + own-premium adopted for motor by the pre-registered rule) need an HS decision.
- Proposals: 8+ (level check as a gate; meaning-vs-stamp test; persistence audit; residual ratio clusters; empty-gap boundary; capacity edge rule; empirical completion check; open-claim selection effect …) → `eval/promotion_cycle_2.md`.

## D. Deliverables — technical
validate_outputs PASS; check_sub passes for both candidates. Levels A: 477 / 423 / 94 (cycle 1: 562 / 390 / 92).

**Data version comparison D1 vs D2** (the measurement that matters): identical rows, identical exposure totals, identical Σ y to the unit, completion within 0.005 by line-year. Column differences are naming (age_band ↔ driver_age_band), weather means vs yearly values, dq-flag names, and two new history features in D2 (hist_prior_claims_policy, hist_years_observed). **Data quality converged at D1.**

Agent baseline holdout (code-graded): D2 0.0978 (motor 0.0658 / buildings 0.0347 / contents 0.0509) vs D1 0.1125 (0.0754 / 0.0760 / 0.0416). Buildings level 1.56 (2023 fire year carried into 2024). The agent's baseline is **not** the measuring instrument: its capacity rule halved rounds to 75 (motor) on one fold and the R-0311 intercept did not hold the level ("explicit level factor" applied) — model-track variance between fresh agents, not a data difference. The data effect is measured with Evan's frozen M0 on D0 vs D2.

## Transcript audit and a contamination finding
Outside-folder access: none in either cycle (tool inputs scanned for `../`, `eval`, `answer_key`, `week2_data`, `week1_output`, repo paths; 0 hits; no web tools; no questions asked).

**Cycle 2 was not a fully fresh agent.** Claude Code's auto-memory wrote `~/.claude/projects/C--Users-Guest1337-harness-run/memory/harness-run-part2-status.md` at the end of cycle 1, and cycle 2's **first tool call** was `cat` of that file (its index is injected into the session context). Recovered content of the cycle-1 note (from the cycle-1 transcript's Write call): deliverables were all produced; "findings.json with 23 findings"; script names `p10_clean → p11_findings → p30_target → p40_baseline`; run Python with PYTHONUTF8=1; open decisions "trend candidate A vs B, IBNER uplift, contents new-business uplift, gender use, 36 excluded pre-inception claims"; the validation rule (one fold 2023→2024, 3 seeds, > 3 seed-sd). It did **not** contain the findings themselves, the schema mapping, the completion method or any numbers beyond those.

Effect on this scorecard: the cycle-2 detection of the 36 pre-inception claims and its list of open decisions are **not independent** of cycle 1 (both were in the note); the environment pitfalls shortened set-up; the rest of the 23 findings (exposure clusters, unit ratio, cohort stamps, MNAR, survivor sample, age-band conflict, gender, weather 2025, reference-table gap …) were not in the note and had to be found from the data and the playbooks. The rule-caught / novel attribution comes from `triggered_by_rules` and stands. Fix for cycle 3: new folder name per cycle and the memory directory deleted before the run (LOOP.md Prepare).

## Verdict (draft)
Harness v2 converted every cycle-1 novel finding into a rule-caught one and the agent spent the freed effort on structure the key never had (survivor sample, history features, empirical completion check) — the resource thesis in one cycle. The pricing-relevant data did not change between D1 and D2 → stop the data track; promote cycle-2 proposals to v3 for the record; hand D2 to the pipeline. The agent-built baseline regressed through its own single-fold capacity choice; that is a modelling-playbook lesson (R-0312 needs a floor and a secondary check), not a data one.
