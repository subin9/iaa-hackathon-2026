"""Cost-based experience history, the Tweedie counterpart of exprate.py.

A Tweedie GBM per line, out of fold by policy, gives every earlier-year row its
expected capped cost. For each target row and key, writes the observed capped
cost C and the expected cost E summed per earlier year, so a blend can test
cost credibility (k + C) / (k + E) with any year decay.
Writes work/expcost_{fold}.parquet with C_{key}_{lag} and E_{key}_{lag}.

usage: expcost.py
"""
import os
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, cap_target
from run import FOLDS
from exp import codes

P = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=7, min_data_in_leaf=2000,
         feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1,
         num_threads=int(os.environ.get("NT", 6)))
KEYS = ("policy_id", "customer_id")


def history(last, ty):
    hist, targets = [], []
    for line in LINES:
        df = load(line)
        tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
        X = codes(to_pandas(tr))
        w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
        y, _ = cap_target(tr["y"].to_numpy(), 0.99)
        base = np.log(y.sum() / w.sum())
        grp = np.array([hash(p) % 5 for p in tr["policy_id"].to_numpy()])
        mu = np.empty(len(y))
        for k in range(5):
            t = grp != k
            m = lgb.train(P, lgb.Dataset(X[t], y[t], init_score=np.log(w[t]) + base), 300)
            mu[~t] = np.exp(base + m.predict(X[~t], raw_score=True)) * w[~t]
        # costs in units of the line's mean cost per claim-free row so lines are comparable
        unit = y.sum() / len(y)
        hist.append(tr.select(*KEYS, "year").with_columns(c=pl.Series(y / unit), e=pl.Series(mu / unit)))
        te = df.filter(pl.col("split") == "test") if ty == 2025 else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
        targets.append(te.select("row_id", *KEYS))
    return pl.concat(hist), pl.concat(targets)


def main():
    for fold, (last, ty) in FOLDS.items():
        hist, tg = history(last, ty)
        hist = hist.with_columns(lag=ty - pl.col("year"))
        out = tg.select("row_id")
        for k in KEYS:
            g = hist.group_by(k).agg([pl.col(v).filter(pl.col("lag") == l).sum().alias(f"{v.upper()}_{k}_{l}")
                                      for v in ("c", "e") for l in range(1, 6)])
            out = out.join(tg.select("row_id", k).join(g, on=k, how="left").drop(k), on="row_id", how="left")
        out.fill_null(0).write_parquet(f"work/expcost_{fold}.parquet")
        print(fold, "done", flush=True)


if __name__ == "__main__":
    main()
