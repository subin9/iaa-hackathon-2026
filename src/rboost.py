"""Boosting on responses with a Tweedie log-link (Hainaut, Trufin and Denuit, 2022).

Each round fits a small tree to the ratio y / mu with weight mu^(2-p) (Fisher scoring)
instead of the Newton gradient LightGBM uses, then multiplies mu by the leaf ratio
raised to the learning rate. LightGBM is only the weighted tree fitter. Saved as
"rb" (lean features, three-leaf trees).

usage: rboost.py ROUNDS [SEEDS]
"""
import sys, os
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, cap_target
from exp import codes
from run import FOLDS, line_trend, LEAN

P = float(os.environ.get("RB_P", 1.4))
LR = float(os.environ.get("RB_LR", 0.1))
TREE = dict(objective="regression", num_leaves=3, min_data_in_leaf=2000, learning_rate=1.0, lambda_l2=10.0,
            feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, verbose=-1, num_threads=int(os.environ.get("NT", 6)))


def fit_predict(tr, te, ty, rounds, seed):
    X = codes(to_pandas(tr, LEAN)); Xt = codes(align_categories(to_pandas(tr, LEAN), to_pandas(te, LEAN)))
    y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    mu = np.full(len(y), y.sum() / w.sum()) * w
    mut = np.full(len(Xt), y.sum() / w.sum())
    ds = lgb.Dataset(X, np.ones(len(y)), free_raw_data=False).construct()
    for r in range(rounds):
        mu_rate = mu / w
        ds.set_label(y / mu); ds.set_weight(mu ** (2 - P))
        m = lgb.train({**TREE, "seed": seed * 1000 + r}, ds, 1)
        step = m.predict(X)
        mu = mu * np.maximum(step, 1e-3) ** LR
        mut = mut * np.maximum(m.predict(Xt), 1e-3) ** LR
    last = int(tr["year"].max())
    return mut * te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))


def main(rounds, seeds):
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            df = load(line)
            tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
            te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
            p = sum(fit_predict(tr, te, ty, rounds, s) for s in range(seeds)) / seeds
            if fold != "test":
                p = p * te["completion"].to_numpy()
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(p)))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/{os.environ.get('RB_NAME', 'rb')}_{fold}.parquet")
        print("rb", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 1)
