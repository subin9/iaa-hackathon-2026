# Promotion triage — cycle 3 retrospective → harness v4 (gate ②)

Source: `runs/cycle_3/retrospective.md` → "Proposed additions to this workspace's practices".
Decision per candidate: ACCEPT / REWRITE / REJECT. Evan: general? implementable? conflicts? HS: actuarially right?

| # | Proposed rule (agent, paraphrased) | Target | Decision | Evan | HS |
|---|---|---|---|---|---|
| 1 | Determine the dominant exposure convention from full-year rows first (inclusive vs exclusive day count), then tabulate the stored÷derived ratio on that basis — otherwise short rows smear across 1.00–2.00 and hide the 360-day spike | data_readiness, amend R-0014 | ACCEPT (fold into R-0014) | pending | ✅ 2026-10-27 |
| 2 | Compute PSI on non-null values and report the null-rate difference separately; when several unrelated columns show the same PSI, suspect the null bin or a join, not the data | adaptation, amend R-0402 | ACCEPT | pending | ✅ 2026-10-27 |
| 3 | Level gate before capacity choice, with a leaf-step limit (e.g. `max_delta_step`) for Tweedie boosters on small data; exclude categoricals whose level count is comparable to the claim count | modeling, amend R-0311/R-0312 | ACCEPT — this is the fix that made the cycle-3 baseline hold its level | pending | ✅ 2026-10-27 |
| 4 | Identify the acquired book explicitly before modelling: which flag singles it out; if none, name the training analogue, its claim count and age-standardised relativity, and compare the model's relativity to it afterwards as a pre-registered table | adaptation, amend R-0410 | ACCEPT (fold into R-0410) | pending | ✅ 2026-10-27 |
| 5 | Treat prediction-year weather as a calendar stamp by default: test each index alone against the train/test label; if the prediction year differs for every address, exclude or replace with an address-level climate summary | data_readiness, amend R-0006 / new | ACCEPT | pending | ✅ 2026-10-27 |
| 6 | Label-does-not-terminate check inside the persistence audit: cross-tab each end-of-period decision with presence next year; a terminating value with near-complete persistence is a semantic defect to query | data_readiness, amend R-0020 | ACCEPT (fold into R-0020) | pending | ✅ 2026-10-27 |
| 7 | Carry two completion variants (spliced and no-tail) in the modelling tables so the borrowed share is visible and re-runnable | target, amend R-0108 | ACCEPT — already the practice in R-0108's text; make it explicit as a table requirement | pending | ✅ 2026-10-27 |
| 8 | Reconciliation ladder as a script output printed by the pipeline, not prose | data_readiness, amend R-0017 | ACCEPT | pending | ✅ 2026-10-27 |

All 8 origin AGENT_RETRO, source_cycle 3. No actuary additions this cycle.
