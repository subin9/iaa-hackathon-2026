# Promotion triage — cycle 4 retrospective → harness v5 (final recorded state, gate ②)

Source: `runs/cycle_4/retrospective.md` → "Proposed additions".

**Decision 2026-10-27 (HS): the data track stops at cycle 4. harness-v4 is frozen as the final executed harness (`harness-final` tag). The proposals below are approved as a backlog — written up here, not deployed into the playbooks — to be executed on the next market, so that the final harness state is one that was actually run.**

| # | Proposed rule (agent, paraphrased) | Target | Decision | Evan | HS |
|---|---|---|---|---|---|
| 1 | Convention first, then clusters, then a wider net (ratio bins beyond the named clusters) | data_readiness, amend R-0014 | ACCEPT (minor) | pending | ✅ backlog 2026-10-27 |
| 2 | Sibling-stability test before imputing policy attributes: an attribute constant within a policy across its rows may be reconstructed from a sibling row; a per-period attribute may not | data_readiness, new rule after R-0018 | **ACCEPT — substantive** (restored ~9k motor parking values; verified) | pending | ✅ backlog 2026-10-27 |
| 3 | Null-bin artefact check in distribution distances | adaptation, R-0402 | already covered by the cycle-3 amendment — REJECT as duplicate | — | ✅ reject (duplicate) |
| 4 | Capacity secondary check must come from the same volume (not a pooled 2-year fold) | modeling, amend R-0312 | ACCEPT | pending | ✅ backlog 2026-10-27 |
| 5 | Year-by-year segment relativities before trusting a model's segment effect | adaptation, amend R-0410 | ACCEPT | pending | ✅ backlog 2026-10-27 |
| 6 | Level gate by line, with a learner-fix order (leaf-step → regularisation → categoricals → explicit factor) | modeling, amend R-0311 | ACCEPT (fold in) | pending | ✅ backlog 2026-10-27 |
| 7 | Leap-year / period-end sanity line in the profile (do full-year rows end on 31 Dec or on day 365?) | data_readiness, new (also closes the thrice-novel F-03) | ACCEPT | pending | ✅ backlog 2026-10-27 |
| 8 | Decision-value persistence cross-tab as a standing check | data_readiness, R-0020 | already in the cycle-3 amendment — REJECT as duplicate | — | ✅ reject (duplicate) |
