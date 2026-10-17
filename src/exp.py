"""Quick experiment harness: train <= 2023, score 2024 (pred x completion), pooled D2."""
import sys, json
import numpy as np, polars as pl, lightgbm as lgb, pandas as pd
from common import LINES, load, to_pandas, align_categories, d2, cap_target

BASE = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=15,
            min_data_in_leaf=2000, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1,
            lambda_l2=10.0, cat_smooth=50, min_data_per_group=500, verbose=-1, num_threads=16)
ROUNDS = (50, 100, 150, 200, 300, 400, 600)


def codes(X):
    for c in X.columns:
        if isinstance(X[c].dtype, pd.CategoricalDtype):
            X[c] = X[c].cat.codes.astype("float32").replace(-1, np.nan)
    return X


def run(cfg, last=2023, vy=2024):
    P = {**BASE, **cfg.get("params", {})}
    ys, ps = [], {r: [] for r in ROUNDS}
    for line in LINES:
        df = load(line).filter(pl.col("split") == "train")
        tr, va = df.filter(pl.col("year") <= last), df.filter(pl.col("year") == vy)
        drop = cfg.get("drop", [])
        X = to_pandas(tr, drop); Xv = align_categories(X, to_pandas(va, drop))
        if cfg.get("codes"):
            X, Xv = codes(X), codes(Xv)
        y, load_f = cap_target(tr["y"].to_numpy(), cfg.get("cap"))
        w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
        wv = va["exposure"].to_numpy() * va["completion"].to_numpy()
        base = np.log(y.sum() / w.sum())
        m = lgb.train(P, lgb.Dataset(X, y, init_score=np.log(w) + base), max(ROUNDS))
        yv = va["y"].to_numpy(); ys.append(yv)
        for r in ROUNDS:
            p = np.exp(np.log(wv) + base + m.predict(Xv, raw_score=True, num_iteration=r)) * load_f
            ps[r].append(p)
    Y = np.concatenate(ys)
    res = {}
    for r in ROUNDS:
        p = np.concatenate(ps[r])
        k = Y.sum() / p.sum()
        res[r] = (round(d2(Y, p), 4), round(d2(Y, p * k), 4), round(k, 3))
    return res


if __name__ == "__main__":
    cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    res = run(cfg)
    best = max(res.items(), key=lambda kv: kv[1][0])
    print(json.dumps(cfg), "| best r", best[0], "d2", best[1][0], "| d2 if A/E=1:", best[1][1], "k", best[1][2])
    print("  ", res)
