# Promotion triage — cycle 2 retrospective → harness v3 (gate ②)

| # | Proposed rule (agent) | Target | Decision | Evan | HS |
|---|---|---|---|---|---|
| 1 | Level check is a gate: Σ prediction / Σ target on training rows must be ≈1 before any fold score is read; fix the learner or apply and report an explicit level factor | modeling, strengthen R-0311 | ACCEPT (rewrite R-0311) | pending | ✅ 2026-10-27 |
| 2 | Meaning test before the stamp test: a feature that separates years is a stamp only if its meaning changes with the calendar; mix features (new_business, tenure, age) are kept and evaluated on the shifted subset | data_readiness, after R-0016 | ACCEPT | pending | ✅ 2026-10-27 |
| 3 | Persistence audit of the first training year (share reappearing next year, end-of-period decisions); complete persistence with no lapses = survivor sample, label it in shift report and validation design | data_readiness, new | ACCEPT — also applies to Part 1 (developed 2021) | pending | ✅ 2026-10-27 |
| 4 | Ratio clusters on the residual after the obvious cluster, and on test files separately | data_readiness, amend R-0014 | ACCEPT (fold into R-0014) | pending | ✅ 2026-10-27 |
| 5 | Empty-gap boundary for unit errors; if no empty interval, bring in a second column | data_readiness, amend R-0013 | ACCEPT (fold into R-0013) | pending | ✅ 2026-10-27 |
| 6 | Capacity grid with a pre-registered edge rule (halve/double to a floor) | modeling, amend R-0312 | ACCEPT with a caveat: require the secondary check to agree and never below a floor of ~100 rounds — the cycle-2 choice of 75 regressed the holdout | pending | ✅ 2026-10-27 (with caveat) |
| 7 | Empirical completion check from the oldest accident year (12-month vs valuation-date cost ratio vs curve) | target, after R-0108 | ACCEPT | pending | ✅ 2026-10-27 |
| 8 | Open-claim selection effect when comparing open vs closed costs | target, amend R-0105 | ACCEPT (text to be taken from retro §8) | pending | ✅ 2026-10-27 |
| A | (ACTUARY) Agent-built baselines vary between fresh runs through single-fold modelling choices; the data effect is measured only with a frozen external model (M0) — eval-side note, not a harness rule | eval/LOOP.md | note | | |

Not in the table when approved — **pending HS yes/no** (both method-level, low risk):

| # | Proposed rule (agent) | Target | Draft |
|---|---|---|---|
| 9 | Free-text noise test: after case/whitespace normalisation, test whether a remaining prefix/suffix variant occurs at the same rate in every base category — uniform rate = random corruption to strip, non-uniform = real attribute to keep as a flag | data_readiness, new | ACCEPT |
| 10 | Reference-table coverage recorded as a findings item with team_query (join channel/product/segment lists to every loading table) | adaptation, amend R-0412 | ACCEPT |
