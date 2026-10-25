"""E13: sampling noise of a best segment multiplier measured on the public leaderboard.

The best factor of a segment on the public rows is m* = sum(y mu^-1/2) / sum(mu^1/2) (the probe solver's U / (f T)). The public rows are a sample of
about a third of the test rows, so m* carries sampling noise that the private rows do not share, and a factor taken from it at face value over-fits.
Here the noise is measured on the emerging training rows: out-of-fold predictions of the final pipeline, then bootstrap draws of as many rows as the
public part of each segment holds. Writes the standard deviation of log m* per segment to work/p2/cell_noise.json (read by shrink_multipliers.py).
usage: e13_cell_noise.py
"""
import sys, json; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2

rng = np.random.default_rng(0)
F = 1.0 / 3.0
res = {}
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil_v_avg_{line}.parquet"), on="row_id")
    ye = em["y"].to_numpy(); o = np.zeros(len(ye))
    for tri, vai in GroupKFold(5).split(em, ye, em["customer_id"].to_numpy()):
        o[vai] = model2.pipeline(em[tri], em[vai], short=model2.SHORT[line], score_is_train=True)
    ok = o > 0; a = ye[ok] / np.sqrt(o[ok]); b = np.sqrt(o[ok])
    te = load(line, "em").filter(pl.col("split") == "test")
    res[line] = {"oof_mstar": float(a.sum() / b.sum()), "n_test": len(te), "nb_share_test": float(te["new_business"].mean()), "pool": (a, b)}
    print(line, "OOF m* (all training rows)", round(res[line]["oof_mstar"], 3), "rows", len(a))

def noise(line, n):
    a, b = res[line]["pool"]; idx = rng.integers(0, len(a), (400, n))
    return float(np.log(a[idx].sum(1) / b[idx].sum(1)).std())

n = {l: res[l]["n_test"] * F for l in LINES}; nbs = {l: res[l]["nb_share_test"] for l in LINES}
seg_rows = {"motor_nb": n["motor"] * nbs["motor"], "buildings_nb": n["buildings"] * nbs["buildings"], "contents_nb": n["contents"] * nbs["contents"],
            "renewal": sum(n[l] * (1 - nbs[l]) for l in LINES), "direct_nb_motor": n["motor"] * 0.19, "male_motor": n["motor"] * 0.5, "age3549_buildings": n["buildings"] * 0.13}
line_of = {"motor_nb": "motor", "buildings_nb": "buildings", "contents_nb": "contents", "renewal": "motor", "direct_nb_motor": "motor", "male_motor": "motor", "age3549_buildings": "buildings"}
out = {k: noise(line_of[k], int(v)) for k, v in seg_rows.items()}
for k in out: print(f"  {k:20s} public rows {int(seg_rows[k]):6d}  sd of log m* {out[k]:.3f}")
json.dump(out, open("work/p2/cell_noise.json", "w"), indent=1)
np.savez("work/p2/oof_pool.npz", **{f"{l}_{k}": v for l in LINES for k, v in zip("ab", res[l]["pool"])})   # row terms y mu^-1/2 and mu^1/2 of the out-of-fold predictions
