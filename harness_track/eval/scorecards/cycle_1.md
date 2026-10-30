# Scorecard — cycle 1 (harness-v1 → data version D1)

Run: 2026-10-25 ~23:15 → 2026-10-26 ~01:05 SGT (≈1h50, budget was 4h) | operator: HS | model: claude-fable-5-1, effort xhigh | run location: `C:\Users\Guest1337\harness_run` (copy outside the repo, `memory/` removed) | interventions: permission prompts → auto mode at 00:00 (no content instruction) | cost/tokens: … (from `/cost`)
Graders: sections A, D → data scientist (DRAFT below by HS/assistant, to be confirmed by Evan) · sections B, C, E → actuary + AI second reader

## A. Detection and treatment (vs answer_key.md) — technical

| # | Answer-key item | Found? | Treatment | Correct? | Notes |
|---|---|---|---|---|---|
| 1 | exposure stored in days (train only) | ✅ F-01, 114 rows | REPAIR from dates (days/365) | ✅ | **Plus a second defect the key missed**: F-02, 493 rows on a 360-day basis (+1.39%); verified exactly (206/121/166). Key's 0.02 tolerance was too loose. |
| 2 | sum_insured ×1000 (train AND test) | ✅ F-03/F-04, 110 train + 239 test | REPAIR ÷1000, decided by premium/sum-insured ratio | ✅ | Counts match key (53/104, 57/135). Ratio rule is better than a value threshold (→ promotion candidate). Description of F-03 says "unit too small"; treatment correct. |
| 3 | claims with loss_date outside any policy period | ✅ F-07, 36 claims | EXCLUDE + team_query | ✅ (defensible) | Attributed to R-0004/R-0007, so rule-caught not novel. Lag-plausibility argument (lags 411–565 d vs p99.5 ≤ 344 d) is new evidence the key did not have. Alternative (shift +1 year) listed in retro. |
| 4 | duplicate claims — none present | ✅ F-06 | negative result logged | ✅ | Also checked (policy, peril, loss_date) collisions. |
| 5 | customer_service_contacts train-only tail | ✅ F-16 | excluded from features | ✅ | Quantified mechanism (0.4 → 3.0 → 5.6 → 8.1 by claim count). |
| 6 | customer_since_year = test-year identifier | ✅ F-14 | excluded; renewal_count kept | ✅ | Found identity customer_since_year ≡ period_year − renewal_count. **Also found campaign_code null ⇔ joined < 2023 (AUC 0.79 alone)** — not in key; verified. |
| 7 | occupation free text | ✅ F-11 (novel) | RECLASSIFY: trim + case → 20 titles + "Self-employed" variants (40 values) | ✅ | 80 raw → 40; plus self_employed flag in modelling tables. Null 12% left as unknown. |
| 8 | block-missing customer fields | ✅ F-12 (novel), reinterpreted | NO_ACTION; MCAR evidence (independent 12% draws across 15 columns, no link to channel/year) | ✅ — key's "block/broker-feed" hypothesis was wrong | Agent's reading is better supported than the key's. |
| 9 | motor nulls (vehicle_age, engine_size_cc, overnight_parking) | ✅ within F-12 | kept as unknown level | ✅ | |
| 10 | expenses: comparison_site commission blank vs channel present | ✅ F-19 (novel), team_query | flagged for premium build | ✅ | |
| — | False alarms | none found so far | | | F-02, F-18, F-23, campaign_code and the Part 1 missing-customer note all verified exactly. F-21 (3 repairers × 80 claims) not verified; descriptive only, no action. |

Beyond the key (all NO_ACTION / flag): F-13 flood_zone MNAR (missing ⇒ lower, nearer river) — modelled as its own level; F-18 ncb_years > years_licensed on 16.4% train / 22.2% test, young bands (verified exactly); F-20 discount_applied = f(channel) with 14% → 77% definition shift; F-23 2024 full-year rows end 30 Dec (verified); F-17 weather has 2025 (treated as unavailable); F-22 reference_policies are test-row copies; retro: **10.0% of developed motor rows reference customers absent from developed customers.parquet** (verified: 98,110 / 979,968) — a Part 1 data issue nobody recorded in Week 1.

Detection rate: 10/10 (+2 real defects the key missed) · correct treatment: 10/10 · false alarms: 0 confirmed
Rule-caught (triggered_by_rules non-empty): 15 · novel (empty): 8 · missed: 0 · time to first novel finding: … (from transcript)

## B. Adaptation decisions — actuarial
- Schema mapping table delivered (age bands, 11+4 construction codes → 4 classes with share evidence, occupation → 20 + self_employed, region unmapped). ☐ HS to confirm construction merge (W vs T).
- Shift report: new-business/broker dominance, age mix, renewal_count collapse, discount definition change all surfaced; adversarial AUC 1.00 → 0.83 → 0.58–0.63 with each exclusion named.
- Frequency / severity / peril mix by line delivered: motor freq +30% vs developed but every peril 40–50% cheaper; buildings same freq with fire 45% of cost on 70 claims; contents freq −15%, same severity. Thin perils labelled.
- Carry-over table: all 16 components filled with evidence file and sensitivity. Combined level uncertainty stated: motor −8/+12%, buildings ±15%, contents ±8%.
- Borrowed assumptions listed with sensitivities (tail 2.1%/0.2%/0.03%; trend +3/+6/+5 vs zero; fire view ±10–15%).
- ☐ HS judgment needed on: trend candidate A vs B; IBNER 0/+6% motor; contents new-business uplift (+15–20% on 76% of rows); gender; fire load; 36 excluded claims; ncb vs licence authority.

## C. Handling of rules that could not be applied — actuarial
- One fold recognised; substitute = primary fold > 3 seed-sd AND not worse on policy-grouped secondary, labelled weaker. Escalated in retro table (13 rules listed with substitute and what was lost). ✅
- Credibility recognised as identity for new business; dropped with reasoning. ✅
- Completion: reverse-time product-limit estimator with truncation correction; tail beyond 540 d borrowed and sized. Both variants carried. ✅ (method is sound; HS to confirm the anchor choice)
- Noise floor re-measured per line from seeds (0.0006 / 0.0042 / 0.0020) rather than assumed. ✅

## D. Deliverables and self-verification (technical)
- validate_outputs.py: PASS (23 findings, 15 rule-attributed, 8 novel; holdout 100% coverage). check_sub passes for both candidate files.
- Reconciliations: exposure raw→cleaned, claims raw→cleaned, Σy = cleaned claims to the cent (27,997,991.57), Σ prediction = Σ y_capped on training rows (intercept in init score).
- Modelling tables: motor/buildings/contents.parquet with row_id, split, year, exposure, completion (two variants), y, y_capped, trend_factor, dq flags, lean features; README lists columns and excluded groups. ☐ Evan gate ①: schema vs pipeline, offsets, leakage in fold design.
- Baseline: single 3-leaf LightGBM Tweedie per line, 3 seeds, rounds re-chosen on the fold (300/600/300). Primary fold D² 0.0731 / 0.0790 / 0.0387.
- Holdout (code-graded, `eval/grade_holdout.py`): **D1_agent_baseline d2_all 0.1125** (motor 0.0754, buildings 0.0760, contents 0.0416 — identical to the agent's own numbers); level ratios 0.95 / 1.27 / 0.93. Floor naive_2023_rate 0.0701.

## E. Retrospective quality — actuarial
- Weakest judgment calls named: 9, each with alternative and reason. ✅
- Proposed rules: 11, all method-level, none contain counts or identifiers. ✅ Candidates to promote → see `eval/promotion_cycle_1.md`.
- Open questions: 10, including two team queries that are genuinely the team's (trend, IBNER) and one Part 1 data question.

## F. Second-reader view
… (to run)

## Verdict (draft)
The harness contributed: every Week 1 check ran and left a negative result where nothing was found; two defects beyond the answer key were found by applying rule methods more carefully than the architect did; leakage, completion, trend and level handling followed the playbooks and escalated exactly where they did not fit. The agent found 8 novel items on its own, three of them actionable (occupation, flood_zone MNAR, campaign_code cohort stamp). Missed: nothing in the key. What enters v2: the 11 proposals after triage (ratio-based unit check, exposure ratio clusters, lag plausibility, cohort-stamp detection, truncation-corrected curve, intercept-in-offset, capacity re-choice, new-business pre-check, like-for-like cap, reconciliation ladder, raw-vs-cleaned guardrail printout).
