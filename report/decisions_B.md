# Actuarial decisions for the Part 2 submission (gate ④ — draft for HS)

Evidence: four independent agent runs (cycles 1–4) on the same data under harness v1–v4; each produced
`adaptation_decisions.md`, `target_notes.md` and `baseline/validation.md`. Numbers below are quoted from those files
(`runs/cycle_N/`). "Level" = predicted CU per exposure-year on the 2025 test book. Decisions are applied to the
data scientist's final model as multipliers (line level, segment rows), not by re-training.

| # | Decision | What the four runs found | Options | Effect on 2025 level | **Recommendation** |
|---|---|---|---|---|---|
| B1 | **Trend** to mid-2025 | No emerging trend can be fitted (one mature year). Developed 2021–23 completed slope ≈ +3 / +6 / +5 %/yr (motor/buildings/contents); developed 2024 motor fell −9% completed (reserving or real). Emerging one-step: motor +4…+7%, buildings −37% (fire), contents −2%. Cycles 3–4 floored motor at 0%. | A: borrow full developed slope (+3/+6/+5) · B: zero · C: half weight (+1.5/+3/+2.5) | A vs B = +4 / +13 / +11 % on level; C = +2.3 / +4.5 / +3.8 % | **C (half weight), applied for 1.5 years.** The only emerging signal (motor) is noisy and the developed market itself flattened in 2024; shrinking a borrowed slope toward zero is the standard treatment for a prior without local credibility. Disclose A and B as the range. |
| B2 | **IBNER** uplift on 2024 open claims | No credible under-reserving signal in any cycle: BI open means equal across years (c1); implied uplift −7/+4/−4 % is a selection artefact (c2); same open shares as developed (c3); like-for-like impossible (c4). Open claims = 38 / 35 / 18 % of 2024 line cost. | 0 · +3 % motor · +6 % motor | ±10 % on open-claim settlement = ±3.8 / ±3.5 / ±1.8 % | **0 (no uplift).** Four runs, none found a signal; state the ±4 % sensitivity. Not testable locally. |
| B3 | **New-business relativity** (76 % of the 2025 book) | *Motor*: pre-model age-standardised NB/renewal = 1.43–1.67 (2023) vs 1.28 (2024); the model prices ≈1.47 (c4), 1.36 (c1). *Contents*: data +20…+30 % (≈100 NB claims, 2023 new policies stayed +25 % in 2024), model ≈1.0–1.03. *Buildings*: 35–65 NB claims, unreadable. | Motor: keep model 1.47 · use 2024-observed 1.28 (c4 candidate C, −11 % on motor). Contents: none · shrunk +10…+15 % on NB rows · full +25 % | Motor −11 % between the two; contents 0 / +8…+11 / +19 % on level | **Motor: keep the model's relativity (between the two years) — this is the main level hypothesis; prepare the 1.28 file as the second candidate (R-0505).** **Contents: shrunk uplift ×1.12 on NB rows** (≈ half credibility of a +25 % signal on 100 claims) → contents level ≈ +9 %. **Buildings: none.** |
| B4 | **Gender** as a rating factor (emerging only; the brief says it may be used) | Fold gain within noise in 2 of 3 lines (motor +0.0023 = 3.8 seed-sd in c1, nil in c2; contents +0.0013–0.0027). | exclude · motor only · all lines | ≈ 0 on level; shape only | **Exclude.** Gain is inside the noise floor and the factor is contested in most regulated markets; a pricing team would not adopt a contested factor for a within-noise gain. Record as a market-rule decision for the team. |
| B5 | **Buildings fire load** | 2023 vs 2024 buildings differ 37–70 % on cost; fire = 45 % of cost on 70 claims; developed fire share 4.2 % of claims vs emerging 6.6 %; expenses table loads cat reinsurance 12 % (vs 6 %). Agent test levels ranged 390 → 478 across cycles. | pooled two-year capped (agents) · borrow developed fire share (−10 %) · 2023 repeats (+15 %) | ±15 % | **Pooled two-year capped level, no adjustment**; the 12 % cat load in `expenses` is evidence the market expects high property loss. This is the line where an external level check (public-score probe ×1.10 on buildings) is most valuable; if probed, shrink 30 % toward the pooled level as in Part 1. |
| B6 | 36 claims with loss dates before policy inception | Four runs: date defects (lags 411–565 d vs p99.5 ≤ 344 d), 0.33 % of incurred; unanimous EXCLUDE + team query | exclude · re-date +1 y · attach to first row | ≤ +0.6 % on 2023 motor if they belonged | **Exclude; keep the team query.** |
| B7 | ncb_years > years_licensed (16 % train / 22 % test, young drivers) | Neither field can be shown wrong; identical pattern in train and test; four runs kept both as delivered | keep both · cap ncb at licence years · drop ncb | shape only | **Keep both as delivered**; flag in the report as a data-definition query for the acquired book. |
| B8 | **Final submission pair** (R-0505: prepare two, select one) | The largest unvalidatable level assumption is the motor NB relativity (B3), not trend. | — | — | **Candidate A** = B1-C trend + model NB relativity + contents ×1.12 NB. **Candidate B** = same with motor NB rows ×0.87 (2024-observed relativity). Select A unless a public-score probe shows the motor level high; record the reasoning in `submissions/log.csv`. |

## Implementation for the pipeline (to Evan)
1. Train the final model on D4 modelling tables (or cleaned tables through your own prep) with the leakage exclusions
   from `findings.json` (customer_since_year, campaign_code, discount_applied, customer_service_contacts,
   renewal_decision, 2025 weather; gender excluded per B4).
2. Post-model multipliers, applied in this order and then renormalised per line to the pre-multiplier line total
   only where stated:
   - contents rows with `new_business = 1`: × 1.12 (no renormalisation — this is a level change);
   - trend to mid-2025 (B1-C): motor × 1.023, buildings × 1.045, contents × 1.038 (if your target already carries a
     trend factor, replace it, do not stack);
   - IBNER: × 1.00.
3. Candidate B: additionally motor rows with `new_business = 1` × 0.87.
4. `check_sub` both files; log both with data_version = D4 and the model version.

## What remains uncertain (for the report, ranked by level effect)
buildings fire load ±15 % · motor new-business relativity ±11 % · trend ±5 % (motor) / −9…+3 % (buildings) /
−8…+3 % (contents) · IBNER ±4 % · completion tail/cap ±2.5 % (motor). These are additive in the worst case; the
report states them as a range per line, not a point.
