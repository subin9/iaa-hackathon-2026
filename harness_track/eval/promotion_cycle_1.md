# Promotion triage — cycle 1 retrospective → harness v2 (gate ②)

Decision per candidate: ACCEPT / REWRITE / REJECT. Evan: general? implementable? conflicts? HS: actuarially right?
Admissible only if it would be sensible advice for a market whose issues we had never seen (method, never location or counts).

| # | Proposed rule (agent) | Target playbook / rule | Draft decision (HS assistant) | Evan | HS |
|---|---|---|---|---|---|
| 1 | Proportionality (ratio) check for unit errors — decide per row on premium/sum-insured ratio, not a value threshold | data_readiness, amend R-0003 | ACCEPT — general, better than the Week 1 threshold | | |
| 2 | Classify exposure mismatches by ratio cluster (365, 365/360, (n−1)/n, ≈1) before repairing | data_readiness, amend R-0001 | ACCEPT | | |
| 3 | Lag-plausibility test for unlinked claims (lags beyond matched p99.5 ⇒ date defect, exclude + query) | data_readiness, amend R-0004 | ACCEPT — the "exclude vs re-date" default is a judgment; keep "query" | | |
| 4 | Cohort-stamp detection: cross-tab value AND nullness of every customer attribute vs join year; single-feature AUC first | data_readiness, new rule after R-0006 | ACCEPT | | |
| 5 | Truncation-corrected (reverse product-limit) lag curve as default for < 3 accident years; borrow only beyond the anchor; carry both variants | target_construction, amend R-0102 | ACCEPT — HS to confirm estimator | | |
| 6 | Intercept in the init score of offset-boosted models; check Σ prediction = Σ target before reading any score | modeling, new rule near R-0301/R-0304 | ACCEPT | | |
| 7 | Re-choose capacity (rounds) from a pre-registered small grid when volume changes by an order of magnitude | modeling, amend R-0301 | ACCEPT | | |
| 8 | New-business pre-model check (age-standardised excess, persistence into year 2) before modelling | adaptation, amend R-0406/R-0407 | ACCEPT | | |
| 9 | Like-for-like large-loss basis across markets (same fixed cap) | adaptation, amend R-0403 | ACCEPT | | |
| 10 | Reconciliation ladder as one table; refuse to proceed while any link is open | data_readiness R-0012 / validation R-0208 | ACCEPT (REWRITE into R-0012) | | |
| 11 | Run check_sub on raw and cleaned history; the difference proves the exposure repair mattered | submission_guardrails, amend R-0501 | ACCEPT | | |
| A | (ACTUARY) MNAR check on nulls: compare covariates of null vs non-null rows before choosing "unknown level" vs imputation | data_readiness | PROPOSE — from F-13 | | |
| B | (ACTUARY) Reference-table completeness vs portfolio: every channel/segment present in the book must have an expense/commission entry | adaptation | PROPOSE — from F-19 | | |
| C | (ACTUARY) Answer-key lesson: tolerance for exposure recomputation must be tight enough to see a 360/365 basis | eval-side note, not a harness rule | note only | | |

Origin for all 1–11: AGENT_RETRO, source_cycle 1. A–B: ACTUARY, source_cycle 1.
