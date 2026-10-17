"""Experiment harness over both validation folds (train <= 2023 score 2024, train <= 2022 score 2023).

Each config is a JSON object:
  params   LightGBM overrides on exp.BASE (objective defaults to Tweedie 1.5)
  cap      target cap quantile (default 0.99)
  feats    true to join work/feats_{line}.parquet
  drop     extra columns to drop
  seeds    number of seeds to average (default 1)
  decay    per-year weight multiplier for older years (1 = flat)
Prints pooled D2 per fold at each round count, and the mean of the two folds.

usage: exp2.py CONFIG_JSONL
"""
import sys, os, json, time
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, d2, cap_target
from exp import BASE, codes

ROUNDS = (100, 150, 200, 300, 400)
FOLDS = ((2023, 2024), (2022, 2023))


def table(line, cfg):
    df = load(line).filter(pl.col("split") == "train")
    if cfg.get("feats"):
        df = df.join(pl.read_parquet(f"work/feats_{line}.parquet"), on="row_id", how="left")
    return df


def fold(cfg, last, vy, tables):
    P = {**BASE, "num_threads": int(os.environ.get("NT", 6)), **cfg.get("params", {})}
    ys, ps = [], {r: [] for r in ROUNDS}
    for line in LINES:
        df = tables[line]
        tr, va = df.filter(pl.col("year") <= last), df.filter(pl.col("year") == vy)
        drop = cfg.get("drop", [])
        X = codes(to_pandas(tr, drop)); Xv = codes(align_categories(to_pandas(tr, drop), to_pandas(va, drop)))
        Xv["year"] = last
        y, load_f = cap_target(tr["y"].to_numpy(), cfg.get("cap", 0.99))
        w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
        wv = va["exposure"].to_numpy() * va["completion"].to_numpy()
        base = np.log(y.sum() / w.sum())
        sw = cfg.get("decay", 1.0) ** (last - tr["year"].to_numpy())
        acc = {r: 0 for r in ROUNDS}
        for s in range(cfg.get("seeds", 1)):
            m = lgb.train({**P, "seed": cfg.get("seed0", 0) + s}, lgb.Dataset(X, y, weight=sw, init_score=np.log(w) + base), max(ROUNDS))
            for r in ROUNDS:
                acc[r] = acc[r] + np.exp(base + m.predict(Xv, raw_score=True, num_iteration=r))
        ys.append(va["y"].to_numpy())
        for r in ROUNDS:
            ps[r].append(acc[r] / cfg.get("seeds", 1) * wv * load_f)
    Y = np.concatenate(ys)
    out = {}
    for r in ROUNDS:
        p = np.concatenate(ps[r])
        out[r] = (d2(Y, p), d2(Y, p * Y.sum() / p.sum()))  # raw and level-matched
    return out


if __name__ == "__main__":
    for line_cfg in open(sys.argv[1]):
        if not line_cfg.strip() or line_cfg.startswith("#"):
            continue
        cfg = json.loads(line_cfg); t = time.time()
        tables = {l: table(l, cfg) for l in LINES}
        res = [fold(cfg, last, vy, tables) for last, vy in FOLDS]
        mean = {r: (res[0][r][1] + res[1][r][1]) / 2 for r in ROUNDS}
        best = max(mean, key=mean.get)
        print(json.dumps(cfg), f"| best r {best} mean(level-matched) {mean[best]:.4f}",
              f"v2024 {res[0][best][0]:.4f}/{res[0][best][1]:.4f} v2023 {res[1][best][0]:.4f}/{res[1][best][1]:.4f}",
              f"| {time.time() - t:.0f}s", flush=True)
        print("   ", {r: round(mean[r], 4) for r in ROUNDS}, flush=True)
