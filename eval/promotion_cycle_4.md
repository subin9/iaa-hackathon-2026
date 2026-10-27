# Promotion triage — cycle 4 retrospective → harness v5 (final recorded state, gate ②)

Source: `runs/cycle_4/retrospective.md` → "Proposed additions". No further run is planned; v5 records the end state.

| # | Proposed rule (agent, paraphrased) | Target | Draft decision | Evan | HS |
|---|---|---|---|---|---|
| 1 | Convention first, then clusters, then a wider net (ratio bins beyond the named clusters) | data_readiness, amend R-0014 | ACCEPT (minor) | | |
| 2 | Sibling-stability test before imputing policy attributes: an attribute constant within a policy across its rows may be reconstructed from a sibling row; a per-period attribute may not | data_readiness, new rule after R-0018 | **ACCEPT — substantive** (restored ~9k motor parking values; verified) | | |
| 3 | Null-bin artefact check in distribution distances | adaptation, R-0402 | already covered by the cycle-3 amendment — REJECT as duplicate | | |
| 4 | Capacity secondary check must come from the same volume (not a pooled 2-year fold) | modeling, amend R-0312 | ACCEPT | | |
| 5 | Year-by-year segment relativities before trusting a model's segment effect | adaptation, amend R-0410 | ACCEPT | | |
| 6 | Level gate by line, with a learner-fix order (leaf-step → regularisation → categoricals → explicit factor) | modeling, amend R-0311 | ACCEPT (fold in) | | |
| 7 | Leap-year / period-end sanity line in the profile (do full-year rows end on 31 Dec or on day 365?) | data_readiness, new (also closes the thrice-novel F-03) | ACCEPT | | |
| 8 | Decision-value persistence cross-tab as a standing check | data_readiness, R-0020 | already in the cycle-3 amendment — REJECT as duplicate | | |
