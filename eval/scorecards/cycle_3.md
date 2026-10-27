# Scorecard — cycle 3 (harness-v3 → data version D3)

Run: 2026-10-27 16:02 → 16:46 SGT (**44 min**, no interventions) | fresh folder `harness_run_c3` (no auto-memory, no prior sessions) | cost $19.09 | 2,274 lines of code

## A. Detection — technical
**25 findings: rule-caught 23 · novel 2 · missed 0.** Three-cycle series: 15/8/0 → 17/6/0 → 23/2/0. All ten answer-key items found again (same treatments, same counts). Negative results now explicit for test-file exposure (F-03) and claim-amount units (F-06).
Rule-caught items that were novel in earlier cycles: 360-day exposure (R-0014), ratio-based ×1000 (R-0013), pre-inception claims (R-0015), cohort stamps (R-0016, R-0019), occupation noise test (R-0021 — "Self-employed" prefix now stripped by the uniform-rate rule), survivor sample (R-0020), reference-table gap (R-0412), acquired-book check (R-0410).
New content this cycle: **F-18** declined_by_insurer does not terminate — all 181 policies declined in 2023 reappear in 2024 (caught by R-0020's persistence audit, verified in the cycle-2 check: 106/57/18 declined rows persist); **F-25** 131 rows with period_start = period_end (exposure 1/365), mostly mid-term-change stubs (novel); **F-24** vehicle_age has no value below 3 in the emerging market (definition difference, R-0401); F-19 the 30-Dec convention (novel again — never promoted).
False alarms: none confirmed.

## B/C/E — actuarial
Completion anchor moved to 540 days with the empirical 12-vs-valuation check (R-0109); sensitivity to the curve cap quantified (±2.5% on 2024 motor ultimate — a new, useful number). Weather excluded entirely as a 2025 calendar stamp (judgment call 1). Contents new-business relativity still not applied (1.2–1.3× in data; ≈+17% on the contents test level if adopted). Trend: borrowed +0/+6/+5 vs none. Proposals: 8 (inclusive-day ratio basis; PSI on non-null + null-rate delta; level gate before capacity with leaf-step limit; identify the acquired book explicitly; prediction-year weather as a stamp; label-does-not-terminate check; carry two completion variants; reconciliation ladder as script output).

## D. Deliverables — technical
validate_outputs PASS; check_sub passes; levels A: 577 / 468 / 99.
**D3 vs D2 vs D1**: rows, exposure and Σ y identical to the unit in all three; completion within 0.03 (motor 2024: 0.819 / 0.815 / 0.793 as the anchor and cap changed). **Three consecutive identical data versions → the data track is closed.**
Agent baseline holdout 0.1065 (motor 0.0766 — best of the three cycles; buildings 0.0427; contents 0.0582 — best). The R-0311 gate worked as a gate: the first fit lost 7–40% of level, the agent stopped, added `max_delta_step`, re-ran. Buildings holdout level 1.56 in every cycle: a 2023-only model cannot know 2024's fire year — a property of the holdout, not a defect.

## Verdict
The thesis held over three points: as rules accumulated (50 → 63 → 67), rule-caught findings rose 15 → 17 → 23, novel fell 8 → 6 → 2, wall-clock fell from 75 min to 44 min at equal cost, and the pricing-relevant data was identical from the first cycle. What the agent did with the freed effort: survivor sample, label semantics, completion-curve sensitivity, acquired-book analogue. Cycle 3 is the clean run (no memory, no interventions) and is the reference for the report. Promote cycle-3 proposals to v4 for the record; no further data cycle.
