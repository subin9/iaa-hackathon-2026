"""E2: use the developed-market prediction as a prior for the emerging market. 5-fold CV grouped by customer on emerging rows.
M0 constant level per line | M1 level x dev (b = 1) | M1b level x dev^b, b fitted | M2 emerging GBM boosted from M1b, 25/50/100 rounds |
M3 emerging-only GBM | M4 emerging GBM with the dev prediction as a feature."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
PD = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.05, num_leaves=3, min_data_in_leaf=2000, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
PE = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.03, num_leaves=3, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
PREM = "prem" in sys.argv
drop_dev = drop_cols(premium=PREM); drop_em = [c for c in drop_cols(premium=True) if c not in ("region", "gender", "self_employed")]
KEYS = ["M0", "M1", "M1b", "M2_25", "M2_50", "M2_100", "M3", "M4"]
dev15 = lambda y, mu: np.sum(4 * y * mu ** -0.5 + 4 * mu ** 0.5)  # Tweedie 1.5 deviance up to constants in mu
out = {k: [] for k in KEYS}; ys = []
for line in LINES:
    dev = load(line, "dev").filter(pl.col("split") == "train"); em = load(line, "em").filter(pl.col("split") == "train")
    X, Xe = features(dev, em, drop_dev)
    yd, lf = cap_target(dev["y"].to_numpy(), 0.99); wd = offset(dev); bd = np.log(yd.sum() / wd.sum())
    md = lgb.train({**PD, "seed": 0}, lgb.Dataset(X, yd, init_score=np.log(wd) + bd), 800)
    lr_dev = md.predict(Xe, raw_score=True) + bd
    y, lfe = cap_target(em["y"].to_numpy(), 0.99); w = offset(em); grp = em["customer_id"].to_numpy()
    XE, _ = features(em, em.head(5), drop_em); XE4 = XE.assign(dev=lr_dev); ye = em["y"].to_numpy(); ys.append(ye)
    o = {k: np.zeros(len(y)) for k in KEYS}
    for tri, vai in GroupKFold(5).split(XE, y, grp):
        b0 = np.log(y[tri].sum() / w[tri].sum()); o["M0"][vai] = np.exp(b0) * w[vai] * lfe
        scale = lambda b, idx: np.exp(b * lr_dev[idx]) * w[idx]
        k1 = y[tri].sum() / scale(1.0, tri).sum(); o["M1"][vai] = k1 * scale(1.0, vai) * lfe
        bb = min(np.linspace(0, 1.4, 29), key=lambda b: dev15(y[tri], scale(b, tri) * y[tri].sum() / scale(b, tri).sum()))
        k = y[tri].sum() / scale(bb, tri).sum(); o["M1b"][vai] = k * scale(bb, vai) * lfe
        m2 = lgb.train({**PE, "seed": 0}, lgb.Dataset(XE.iloc[tri], y[tri], init_score=np.log(scale(bb, tri)) + np.log(k)), 100)
        for r in (25, 50, 100):
            o[f"M2_{r}"][vai] = np.exp(m2.predict(XE.iloc[vai], raw_score=True, num_iteration=r) + np.log(scale(bb, vai)) + np.log(k)) * lfe
        m3 = lgb.train({**PE, "seed": 0}, lgb.Dataset(XE.iloc[tri], y[tri], init_score=np.log(w[tri]) + b0), 100)
        o["M3"][vai] = np.exp(m3.predict(XE.iloc[vai], raw_score=True) + b0) * w[vai] * lfe
        m4 = lgb.train({**PE, "seed": 0}, lgb.Dataset(XE4.iloc[tri], y[tri], init_score=np.log(w[tri]) + b0), 100)
        o["M4"][vai] = np.exp(m4.predict(XE4.iloc[vai], raw_score=True) + b0) * w[vai] * lfe
    print(line, "b", round(bb, 2), {k: round(d2(ye, v), 4) for k, v in o.items()}, flush=True)
    for k in KEYS: out[k].append(o[k])
Y = np.concatenate(ys)
print("pooled", {k: round(d2(Y, np.concatenate(v)), 4) for k, v in out.items()})
