"""E24: a joint prior. The per-peril LightGBM is trained on the developed rows together with the emerging training rows (weight P2_W, market flag is_em,
optionally gender and region via P2_KEEP), so the trees can split the emerging rows away from the developed ones where the emerging data supports it,
instead of learning only from the developed market. For CV each of the five folds (the folds of e21/e22) gets its own prior trained without that fold's
emerging rows; the last file is trained on every emerging training row and scores the 2025 rows.
Writes work/p2/devperil{TAG}_k{fold}_{line}.parquet and work/p2/devperil{TAG}_{line}.parquet. Run from the tree that holds the tables (work/clean)."""
import sys, os; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
PD = dict(objective="tweedie", tweedie_variance_power=1.6, learning_rate=0.05, num_leaves=3, min_data_in_leaf=2000, feature_fraction=0.7, bagging_fraction=0.8,
          bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=int(os.environ.get("NT", 8)))
ROUNDS, W = 600, float(os.environ.get("P2_W", "1"))

for line in LINES:
    dev = load(line, "dev").filter(pl.col("split") == "train"); em = load(line, "em").sort("row_id")
    cols = [c for c in dev.columns if c in em.columns]
    dev = dev.select(cols).with_columns(is_em=pl.lit(0)); em = em.select(cols).with_columns(is_em=pl.lit(1))
    tr_idx = np.where(em["split"].to_numpy() == "train")[0]; emt = em[tr_idx]
    folds = [vai for _, vai in GroupKFold(5).split(emt, emt["y"].to_numpy(), emt["customer_id"].to_numpy())]
    perils = sorted(c[2:] for c in dev.columns if c.startswith("y_"))
    for k in list(range(5)) + [None]:
        keep = tr_idx if k is None else np.setdiff1d(tr_idx, tr_idx[folds[k]])
        tr = pl.concat([dev, em[keep]], how="vertical_relaxed"); wt = np.r_[np.ones(len(dev)), np.full(len(keep), W)]
        X, Xe = features(tr, em, drop_cols())
        out = {"row_id": em["row_id"]}
        for p in perils:
            y, lf = cap_target(tr[f"y_{p}"].to_numpy(), 0.995)
            w = np.maximum(tr["exposure"].to_numpy() * tr[f"compk_{p}"].to_numpy(), 1e-6); b = np.log(y.sum() / w.sum())
            raw = np.mean([lgb.train({**PD, "seed": s}, lgb.Dataset(X, y, weight=wt, init_score=np.log(w) + b), ROUNDS).predict(Xe, raw_score=True) for s in range(3)], 0)
            out[f"lrp_{p}"] = raw + b + np.log(lf)
        name = f"work/p2/devperil{TAG}" + ("" if k is None else f"_k{k}") + f"_{line}.parquet"
        pl.DataFrame(out).write_parquet(name); print(line, "fold", k, "written", name, flush=True)
