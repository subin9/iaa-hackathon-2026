"""E1: emerging-only LightGBM, 5-fold CV grouped by customer over the 2023-24 rows (completion-adjusted offset)."""
import sys, json; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
VAR = {
    "lean_noprem": dict(drop=drop_cols(premium=False)),
    "lean_prem": dict(drop=drop_cols(premium=True)),
    "lean_prem_wx": dict(drop=drop_cols(premium=True, weather=True)),
    "lean_prem_mkt": dict(drop=[c for c in drop_cols(premium=True) if c not in ("region", "gender", "self_employed")]),
    "all_prem": dict(drop=[c for c in drop_cols(premium=True, lean=False) if c not in ("region", "gender", "self_employed", "branch_id", "campaign_code", "marketing_segment")]),
}
P = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.03, num_leaves=3, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
ROUNDS = (100, 200, 300, 500, 800)
names = sys.argv[1:] or list(VAR)
for name in names:
    res = {r: [] for r in ROUNDS}; ys = []
    for line in LINES:
        em = load(line, "em").filter(pl.col("split") == "train")
        X, _ = features(em, em.head(5), VAR[name]["drop"])
        y, load_f = cap_target(em["y"].to_numpy(), 0.99); w = offset(em); base = np.log(y.sum() / w.sum())
        oof = {r: np.zeros(len(y)) for r in ROUNDS}
        for tri, vai in GroupKFold(5).split(X, y, em["customer_id"].to_numpy()):
            m = lgb.train({**P, "seed": 0}, lgb.Dataset(X.iloc[tri], y[tri], init_score=np.log(w[tri]) + base), max(ROUNDS))
            for r in ROUNDS:
                oof[r][vai] = np.exp(base + m.predict(X.iloc[vai], raw_score=True, num_iteration=r)) * w[vai] * load_f
        ys.append(em["y"].to_numpy())
        for r in ROUNDS: res[r].append(oof[r])
    Y = np.concatenate(ys)
    print(name, {r: round(d2(Y, np.concatenate(res[r])), 4) for r in ROUNDS}, flush=True)
