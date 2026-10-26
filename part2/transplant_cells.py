"""Carry the leaderboard-calibrated cell levels of one submission over to a new base model: inside each of the twelve cells of probe_solve_cells.py the new
base keeps its own relativities and is rescaled to the cell total of the calibrated file. Used for v9 (v7's cell totals on the power 1.6 prior average).
usage: transplant_cells.py CALIBRATED.csv NEW_BASE.csv OUT.csv"""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
import segments, submission
from probe_solve_cells import cells

cal, new = pl.read_csv(sys.argv[1]), pl.read_csv(sys.argv[2])
d = segments.test_frame(new); cid, names = cells(d); K = len(names)
c = d.select("row_id").join(cal, on="row_id", how="left")["prediction"].to_numpy(); n = d["prediction"].to_numpy()
f = np.bincount(cid, c, K) / np.bincount(cid, n, K)
for k, nm in enumerate(names): print(f"  {nm:34s} rows {np.sum(cid == k):6d}  factor {f[k]:.4f}")
out = d.with_columns(prediction=pl.Series(n * f[cid])).select("row_id", "prediction")
r = out.join(cal, on="row_id", suffix="_cal").select(pl.col("prediction") / pl.col("prediction_cal")).to_series().to_numpy()
print("ratio to the calibrated file: p1, p50, p99", np.round(np.quantile(r, [0.01, 0.5, 0.99]), 4), "max |log|", round(float(np.abs(np.log(r)).max()), 4),
      "| totals", round(float(c.sum())), round(float(out["prediction"].sum())))
submission.write(out, sys.argv[3])
