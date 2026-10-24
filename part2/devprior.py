"""Developed-market prior: shallow lean LightGBM per line trained on all developed 2021-24 rows, scoring every emerging row.
Writes work/p2/devprior_{line}.parquet with row_id and the log rate per exposure year (3 seeds averaged in log space).
usage: devprior.py [prem]   (prem keeps written_premium, premium_rate and discount_applied as features)"""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from lib import *
PD = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.05, num_leaves=3, min_data_in_leaf=2000, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
PREM = "prem" in sys.argv
for line in LINES:
    dev = load(line, "dev").filter(pl.col("split") == "train"); em = load(line, "em")
    X, Xe = features(dev, em, drop_cols(premium=PREM))
    yd, lf = cap_target(dev["y"].to_numpy(), 0.99); wd = offset(dev); bd = np.log(yd.sum() / wd.sum())
    raw = np.mean([lgb.train({**PD, "seed": s}, lgb.Dataset(X, yd, init_score=np.log(wd) + bd), 800).predict(Xe, raw_score=True) for s in range(3)], 0)
    pl.DataFrame({"row_id": em["row_id"], "lr_dev": raw + bd + np.log(lf)}).write_parquet(f"work/p2/devprior{'_prem' if PREM else ''}{TAG}_{line}.parquet")
    print(line, "done; mean dev rate on emerging", round(float(np.exp(raw + bd + np.log(lf)).mean()), 1), flush=True)
