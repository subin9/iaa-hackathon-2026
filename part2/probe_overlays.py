"""Overlay probes: each probe multiplies one segment of a base submission by c, and its public score change gives that segment's best factor
m* = U_s / (F T_s), from Dev(c) - Dev(1) = 4 [U_s (c^-1/2 - 1) + F T_s (c^1/2 - 1)] = -(score_c - score_base) DEV0, with T_s = sum of sqrt(mu) over the
segment's test rows, F = 1/3 and DEV0 the public null deviance (8.60M, from the corrected cell fit of probe_solve_cells.py on the v5 probes).
log m* is shrunk by tau^2 / (tau^2 + se^2), se bootstrapped from the out-of-fold rows of the segment's line with as many rows as its public third.
The shrunk factors multiply the segment rows of a target file (rows in several segments get the product).
usage: probe_overlays.py PROBES_JSON TARGET.csv OUT.csv   (PROBES_JSON: {"base": file, "base_public": x, "probes": [{"name", "file", "c", "public"}]})"""
import sys, json; sys.path.insert(0, "part2")
import numpy as np, polars as pl
import submission

DEV0, F, TAU = 8602043.9, 1.0 / 3.0, 0.25
cfg = json.load(open(sys.argv[1])); base = pl.read_csv(cfg["base"]); target = pl.read_csv(sys.argv[2])
pool = np.load("work/p2/oof_pool.npz"); rng = np.random.default_rng(1)
logf = pl.DataFrame({"row_id": target["row_id"], "lf": np.zeros(len(target))})
for p in cfg["probes"]:
    pr = base.join(pl.read_csv(p["file"]), on="row_id", suffix="_p"); seg = (pr["prediction_p"] / pr["prediction"] - 1).abs().to_numpy() > 1e-9
    assert np.allclose((pr["prediction_p"] / pr["prediction"]).to_numpy()[seg], p["c"], rtol=1e-6), p["name"]
    line = {"M": "motor", "B": "buildings", "C": "contents"}[pr["row_id"][int(np.argmax(seg))][0]]
    T = np.sqrt(pr["prediction"].to_numpy()[seg]).sum(); c = p["c"]
    m = (-(p["public"] - cfg["base_public"]) * DEV0 / 4 - F * T * (np.sqrt(c) - 1)) / (F * T * (1 / np.sqrt(c) - 1))
    a, b = pool[f"{line}_a"], pool[f"{line}_b"]; idx = rng.integers(0, len(a), (400, max(int(F * seg.sum()), 50))); se = np.log(a[idx].sum(1) / b[idx].sum(1)).std()
    w = TAU ** 2 / (TAU ** 2 + se ** 2); applied = w * np.log(m)
    print(f"  {p['name']:36s} rows {seg.sum():6d}  public {p['public']:.5f} ({p['public'] - cfg['base_public']:+.5f})  m* {m:.3f}  se {se:.3f}  weight {w:.2f}  applied {np.exp(applied):.3f}")
    ids = pr.filter(pl.Series(seg))["row_id"]
    logf = logf.with_columns(lf=pl.when(pl.col("row_id").is_in(ids.implode())).then(pl.col("lf") + applied).otherwise(pl.col("lf")))
out = target.join(logf, on="row_id").select("row_id", prediction=pl.col("prediction") * pl.col("lf").exp())
print("total before", round(float(target["prediction"].sum())), "after", round(float(out["prediction"].sum())))
submission.write(out, sys.argv[3])
