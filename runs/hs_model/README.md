# Actuary-built model (unoptimised recipe) — data-effect ladder

`train_hs.py` = the harness modelling recipe (3-leaf LightGBM Tweedie, lr 0.02, 300 rounds, completion offset + intercept,
cap multiplier, 3 seeds, R-0311 level gate) with the signed decisions applied as post-model multipliers
(`report/decisions_B.md`). The model is held fixed; only the data version changes. `prep_raw.py` builds a naive
modelling table from any raw-schema folder (claims linked by loss date, cap at p99, no other preparation).

| cell | data version | prep | tag / file | holdout D² (2023→2024) | 2025 level A (motor / bldg / cont) | public LB |
|---|---|---|---|---|---|---|
| 4a | raw emerging tables | naive, no IBNR completion | `raw_nocomp` | 0.0656 | 334 / 328 / 81 | **0.05891** (below the host's line-average baseline 0.07319) |
| 4b | raw | naive + D4 completion joined | `raw_comp` | 0.0584 | 385 / 331 / 83 | — |
| 4c | raw + exposure recomputed from dates only | naive, no completion | `raw_expfix` | 0.0753 | 463 / 472 / 104 | (to submit) |
| 4d | D4 cleaned tables (all repairs) | naive, no completion | `cleaned_nocomp` | 0.0969 | 458 / 480 / 104 | (to submit) |
| 4e | D4 cleaned tables | naive + D4 completion | `cleaned_comp` | 0.1006 | 536 / 481 / 106 | — |
| 2  | D4 modelling tables (repairs + completion + mapped features + history) | harness | `D4` (`submission_A.csv`) | 0.0995 | 538 / 441 / 107 | **0.13030** |

Reading: the exposure day-count rows (114) deflate the raw model's level by ~23% through the level gate (train total
1.30 → factor 0.77); the remaining repairs — sum_insured ×1000 above all — add +0.02 on the holdout, because an
extra-trees learner draws split thresholds uniformly between min and max, so 110 rows at ×1000 make `sum_insured`
useless for property; completion moves the 2025 motor level +17% (458 → 536), which the reported-basis holdout
barely rewards but the leaderboard will. Leaderboard noise is ≈0.0016 pairwise; read differences against it.

Files for the leaderboard ladder (one UTC day, ≤10 slots): `submission_A_raw_nocomp.csv` (4a), `submission_A_raw_expfix.csv` (4c),
`submission_A_cleaned_nocomp.csv` (4d), `submission_A.csv` (2). Cells 1 and 3 are the data scientist's frozen model on D4 and D0.

## Leaderboard reading (2026-10-29)
Data effect with the model held fixed: 0.059 → 0.130 (+0.071). The raw cell sits *below* the host's line-average
baseline (0.073): 114 day-count exposure rows push the level gate to ×0.77 and deflate every 2025 prediction by a
quarter, so an unrepaired file is worse than knowing nothing but the line averages. Model effect with the data held
fixed (D4): 0.130 (fixed recipe, emerging data only, pre-probe levels) → 0.176 (DS pipeline: developed-market prior,
per-peril levels, corrections, probed cell levels; v13). Both effects are large and they are not additive: the DS
pipeline already repairs the large defects itself, which is why cleaned files alone moved *it* by only +0.00009.
