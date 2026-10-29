# Scorecard — cycle N (harness-vN → data version D_N)

Run: start … end … | operator: … | interventions: … | cost/tokens: …
Graders: sections A, D → data scientist · sections B, C, E → actuary + AI second reader (notes attached)

## A. Detection and treatment (vs answer_key.md) — technical
| # | Answer-key item | Found? | Treatment | Correct? | Notes |
|---|---|---|---|---|---|
| 1 | exposure stored in days (train only) | | | | |
| 2 | sum_insured ×1000 (train AND test) | | | | fixing test rows matters |
| 3 | claims with loss_date outside any policy period | | | | NEW type |
| 4 | duplicate claims — none present | | | | did it check and say so? |
| 5 | customer_service_contacts train-only tail | | | | |
| 6 | customer_since_year = test-year identifier | | | | |
| 7 | occupation free text (case/space variants, prefix, nulls) | | | | NEW type |
| 8 | block-missing customer fields | | | | NEW type; linked to channel? |
| 9 | motor nulls (vehicle_age, engine_size_cc, overnight_parking) | | | | |
| 10 | expenses: comparison_site commission blank vs channel present | | | | report flag |
| — | False alarms (issues reported that are not issues) | | | | list |

Detection rate: …/10 · correct treatment: …/found · false alarms: …
Rule-caught (triggered_by_rules non-empty): … · novel (empty): … · missed: … · time to first novel finding: …

## B. Adaptation decisions — actuarial
- Schema mapping table delivered and correct? (age bands, construction codes, missing columns)
- Shift report: did it surface new-business/broker dominance, age-mix shift, renewal_count collapse?
- Did it decompose frequency / severity / peril mix developed vs emerging?
- Per-component carry-over table filled with evidence and uncertainty?
- Borrowed assumptions (development tail, sparse perils) made visible with sensitivity?

## C. Handling of rules that could not be applied — actuarial
- Did it notice only one time fold exists? What substitute did it propose? Did it escalate?
- Policy-level credibility: did it recognise it is identity for new business?

## D. Deliverables and self-verification (technical)
- validate_outputs.py pass? Reconciliations present (row counts, totals before/after)?
- Modelling tables usable by the pipeline (columns, completion, offsets)?
- Baseline (stretch): fold score, check_sub output, plausibility of line levels.
- Holdout: `python eval/grade_holdout.py runs/cycle_N/baseline/holdout_2024.csv --label D_N_M0 --append eval/holdout_results.csv` → D² all / by line, coverage, level ratio. Floor: naive_2023_rate 0.068.

## E. Retrospective quality — actuarial
- Weakest judgment calls named? Proposed rules general (method, not location)?
- Candidates to promote (→ registry): …

## F. Second-reader view (if run)
…

## Verdict
What the harness contributed · what it missed · what enters v(N+1).
