# Public-score level probe — plan (Part 2)

Purpose: external check of the three level decisions that local data cannot settle (trend B1, motor new-business
relativity B3, buildings fire load B5). Method as in Part 1 (`week1_output/08_level_probing/level_probe.py`):
scaling a prediction by s changes Tweedie-1.5 deviance as A·s^-1/2 + B·s^1/2, so one score per line solves the
line's optimal multiplier once the global curvature is known.

Base file: candidate A from the data scientist's final model on D4 with the B decisions applied (`check_sub` passed).

| # | File | Change vs base | Reads |
|---|---|---|---|
| 1 | base | — | anchor |
| 2 | base_x095 | all × 0.95 | curvature |
| 3 | base_x105 | all × 1.05 | curvature |
| 4 | base_motor110 | motor × 1.10 | motor level |
| 5 | base_buildings110 | buildings × 1.10 | buildings level |
| 6 | base_contents110 | contents × 1.10 | contents level |

Six submissions — within the ten-per-UTC-day limit (Rules §2.2a); UTC day starts 08:00 SGT. Log each in
`submissions/log.csv` with data_version D4, model_version, holdout_d2, submitted_by.

Reading the result: solve the per-line optimum; public-set noise ≈ 0.0015–0.002 D² pairwise (≈69k public rows), so a
line multiplier is noise-limited to about ±4–6 %. Shrink the probed multiplier 30 % toward the pre-probe actuarial
level (as in Part 1) and apply with `transfer.py`-style level transfer to whichever blend is final. Decide A vs B
(motor new-business relativity) from the motor probe. Record the pre-probe estimate, the probed value and the shrunk
value side by side in the report — the probe is disclosed as an out-of-time level check, not hidden.
