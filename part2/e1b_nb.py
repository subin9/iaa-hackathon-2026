"""E1b: does the new-business flag, channel or tenure carry signal in the emerging market, after the other factors?
Per-line CV D2 (grouped by customer, 150 rounds) for feature-set variants; also D2 on the new-business rows alone."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
P = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.03, num_leaves=3, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
base = [c for c in drop_cols(premium=True) if c not in ("region", "gender", "self_employed")]
NB = ["new_business", "renewal_count"]
V = {"base": base,
     "+NB": [c for c in base if c not in NB],
     "+NB+tenure": [c for c in base if c not in NB + ["tenure_years"]],
     "+NB+channel": [c for c in base if c not in NB + ["channel"]],
     "+NB+channel+payment": [c for c in base if c not in NB + ["channel", "payment_method"]],
     "+hist": [c for c in base if c not in NB + ["pol_nclaims", "pol_cost", "pol_nclaims_1y", "cust_nclaims", "cust_cost", "cust_nclaims_1y"]]}
R = 150
for name, drop in V.items():
    ys, ps, nbs = [], [], []; per = {}
    for line in LINES:
        em = load(line, "em").filter(pl.col("split") == "train")
        X, _ = features(em, em.head(5), drop)
        y, load_f = cap_target(em["y"].to_numpy(), 0.99); w = offset(em); b0 = np.log(y.sum() / w.sum()); oof = np.zeros(len(y))
        for tri, vai in GroupKFold(5).split(X, y, em["customer_id"].to_numpy()):
            m = lgb.train({**P, "seed": 0}, lgb.Dataset(X.iloc[tri], y[tri], init_score=np.log(w[tri]) + b0), R)
            oof[vai] = np.exp(b0 + m.predict(X.iloc[vai], raw_score=True)) * w[vai] * load_f
        ye = em["y"].to_numpy(); ys.append(ye); ps.append(oof); nbs.append(em["new_business"].to_numpy()); per[line] = round(d2(ye, oof), 4)
    Y, Q, N = np.concatenate(ys), np.concatenate(ps), np.concatenate(nbs)
    print(f"{name:22s} pooled {d2(Y, Q):.4f}  NB rows {d2(Y[N], Q[N]):.4f}  renewal rows {d2(Y[~N], Q[~N]):.4f}  per line {per}", flush=True)
