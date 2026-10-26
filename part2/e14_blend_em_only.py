"""E14: does an emerging-only model add anything to the transfer pipeline? Same 5 folds grouped by customer; the two out-of-fold predictions are
blended in log space (the blend is then put back on the pipeline's total, since the pipeline is calibrated). Prints pooled and per-line D2 by weight."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
import model2

P = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.03, num_leaves=3, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
ROUNDS = 300
DROP = [c for c in drop_cols(premium=True) if c not in ("region", "gender", "self_employed")]   # e1 variant lean_prem_mkt
W = (0.0, 0.1, 0.2, 0.3, 0.5)
ys, A, B = [], [], []
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil_v_avg_{line}.parquet"), on="row_id")
    y = em["y"].to_numpy(); folds = list(GroupKFold(5).split(em, y, em["customer_id"].to_numpy()))
    X, _ = features(em.select([c for c in em.columns if not c.startswith(("lrp_", "y_", "n_", "compk_"))]), em.head(5), DROP)
    yc, load_f = cap_target(y, 0.99); w = offset(em); base = np.log(yc.sum() / w.sum())
    a, b = np.zeros(len(y)), np.zeros(len(y))
    for tri, vai in folds:
        a[vai] = model2.pipeline(em[tri], em[vai], short=model2.SHORT[line], score_is_train=True)
        m = lgb.train({**P, "seed": 0}, lgb.Dataset(X.iloc[tri], yc[tri], init_score=np.log(w[tri]) + base), ROUNDS)
        b[vai] = np.exp(base + m.predict(X.iloc[vai], raw_score=True)) * w[vai] * load_f
    ys.append(y); A.append(a); B.append(b)
    print(line, {wt: round(d2(y, np.exp((1 - wt) * np.log(a) + wt * np.log(b)) * a.sum() / np.exp((1 - wt) * np.log(a) + wt * np.log(b)).sum()), 4) for wt in W}, flush=True)
Y, A, B = np.concatenate(ys), np.concatenate(A), np.concatenate(B)
print("pooled", {wt: round(d2(Y, np.concatenate([np.exp((1 - wt) * np.log(a) + wt * np.log(b)) * a.sum() / np.exp((1 - wt) * np.log(a) + wt * np.log(b)).sum()
                                                  for a, b in zip(np.split(A, np.cumsum([len(v) for v in ys])[:-1]), np.split(B, np.cumsum([len(v) for v in ys])[:-1]))])), 4) for wt in W})
