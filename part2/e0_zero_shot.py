"""E0: train the shallow lean LightGBM on all developed rows (2021-2024), score emerging 2023-24 rows with no emerging data."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from lib import *
PREM = len(sys.argv) > 1 and sys.argv[1] == "prem"
P = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.05, num_leaves=3, min_data_in_leaf=2000, feature_fraction=0.7,
         bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
parts, per_year = [], []
for line in LINES:
    dev = load(line, "dev").filter(pl.col("split") == "train"); em = load(line, "em").filter(pl.col("split") == "train")
    drop = drop_cols(premium=PREM)
    X, Xe = features(dev, em, drop)
    y, load_f = cap_target(dev["y"].to_numpy(), 0.99)
    w = offset(dev); base = np.log(y.sum() / w.sum())
    m = lgb.train({**P, "seed": 0}, lgb.Dataset(X, y, init_score=np.log(w) + base), 800)
    p = np.exp(base + m.predict(Xe, raw_score=True)) * offset(em) * load_f
    ye = em["y"].to_numpy(); ps = p * ye.sum() / p.sum(); parts.append((ye, ps))
    print(line, "per-line level factor", round(ye.sum() / p.sum(), 3), "D2 with the line level matched", round(d2(ye, ps), 4))
    for yr in (2023, 2024):
        k = (em["year"] == yr).to_numpy()
        print(line, yr, "D2", round(d2(ye[k], p[k]), 4), "level-matched", round(d2(ye[k], p[k] * ye[k].sum() / p[k].sum()), 4), "A/E", round(ye[k].sum() / p[k].sum(), 3))
print("pooled D2, each line level-matched:", round(pooled_d2(parts)[0], 4))
