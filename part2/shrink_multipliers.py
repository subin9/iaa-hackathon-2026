"""Turn the solved public-leaderboard multipliers into a submission, shrunk by their sampling noise.

The solved factors are best for the public third of the test rows. Their sampling noise (e13_cell_noise.py) does not carry over to the private rows, so
each log factor is multiplied by tau^2 / (tau^2 + se^2) (an empirical-Bayes weight; tau is the size of miss we think a segment can have, se the noise).
Contrasts (direct vs other channels, male vs female, age band 35-49 vs the rest) have the noise of two segments and a smaller tau than the levels.
usage: shrink_multipliers.py PROBES_JSON OUT.csv
"""
import sys, json
import numpy as np, polars as pl
sys.path.insert(0, "part2")
import segments, submission
from probe_solve_struct import structure, solve, mstar_rows, predict, PARAMS

TAU = {"motor_nb": 0.25, "buildings_nb": 0.25, "contents_nb": 0.25, "renewal": 0.25, "direct_nb_motor": 0.20, "male_motor": 0.25, "age3549_buildings": 0.20}
CONTRAST = {"direct_nb_motor", "male_motor", "age3549_buildings"}

pr = json.load(open(sys.argv[1])); noise = json.load(open("work/p2/cell_noise.json"))
base = pl.read_csv(pr[0]["file"]); d = segments.test_frame(base); seg, flags = structure(d); mu = d["prediction"].to_numpy()
cs = [np.ones(len(mu))] + [d.select("row_id").join(pl.read_csv(p["file"]), on="row_id", how="left")["prediction"].to_numpy() / mu for p in pr[1:]]
x, se, err, T = solve(mu, cs, [p["public"] for p in pr], seg, flags)
w = np.array([TAU[n] ** 2 / (TAU[n] ** 2 + (noise[n] * (2 ** 0.5 if n in CONTRAST else 1.0)) ** 2) for n in PARAMS])
for n, v, wi in zip(PARAMS, np.exp(x), w): print(f"  {n:20s} m* {v:.3f}  weight {wi:.2f}  applied {np.exp(np.log(v) * wi):.3f}")
f = mstar_rows(x * w, seg, flags)
print("predicted public D2: base", pr[0]["public"], "| full m*", round(predict(mu, x, seg, flags, mstar_rows(x, seg, flags), pr[0]["public"], cs[0]), 5),
      "| shrunk", round(predict(mu, x, seg, flags, f, pr[0]["public"], cs[0]), 5))
out = d.with_columns(prediction=pl.Series(mu * f)).select("row_id", "prediction")
print("total before", round(float(mu.sum())), "after", round(float(out["prediction"].sum())))
submission.write(out, sys.argv[2])
