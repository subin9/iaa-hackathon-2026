# Scorecard — cycle 4 (harness-v4 → data version D4)

Run: 2026-10-27 ≈17:08 → 18:07 SGT (59 min, no interventions) | fresh folder `harness_run_c4` | cost $22.29 | API 41m 53s | 2,011 lines

## A. Detection — technical
**25 findings: rule-caught 23 · novel 2 · missed 0.** Four-cycle series: 15/8 → 17/6 → 23/2 → 23/2. The two novel items are the 30-December period convention (found in cycles 1, 3 and 4; never promoted — promote now as a profile check) and a constant column (compulsory_excess single value per line). **No novel finding of substance → the formal stopping criterion is met.**

New content under existing rules: **F-18 (R-0018) sibling reconstruction** — time-invariant policy attributes (overnight_parking, security_level, high_value_items, smoke_alarms, engine_size_cc, vehicle_age) are constant within a policy (verified: 0 of 25,583 multi-row motor policies vary), so nulls were filled from a sibling row of the same policy: motor overnight_parking nulls 5,697 → 173 (train) and 10,859 → 7,219 (test); 9,164 values restored, matching the independent count exactly. days_unoccupied correctly left alone (per-period). This is the first cycle to change the cleaned tables beyond cycle 1 — and the kind of finding that needs the easy ones out of the way first. F-25 applies the amended R-0105 (open-claim selection effect) and reads the IBNER view correctly. F-14 tests missed_payments_12m under R-0005 and keeps it with evidence.

## D. Data version and baseline
D4 = D3 = D2 = D1 on rows, exposure and Σ y; completion 0.817 (anchor varies 0.79–0.82 across cycles — the ±2.5% cap sensitivity cycle 3 quantified). Feature completeness improved by F-18. **D4 is the hand-off version** (same targets, fewer nulls).
Agent baseline holdout 0.1031 (motor 0.0710 / buildings 0.0306 / contents 0.0718 — contents best of four); buildings level 1.73 (same holdout property as every cycle).

## E. Retrospective
8 proposals (convention first/clusters/wider net; sibling-stability test before imputing; null-bin artefact in distances; capacity secondary check from the same volume; year-by-year segment relativities before trusting a model's segment effect; level gate by line with a learner-fix order; leap-year sanity line; decision-value persistence cross-tab as a standing check). Most are refinements of v3/v4 rules; the sibling-stability test is the one substantive addition.

## Verdict
Stop. Four cycles: rule-caught 15 → 17 → 23 → 23, novel 8 → 6 → 2 → 2 (both trivial), missed 0 throughout, effort constant (API 45 / 53 / 41 / 42 min; ~$20 each). The data converged on targets at cycle 1 and on feature completeness at cycle 4. Promote the cycle-4 proposals to v5 as the final recorded harness state; no further run.
