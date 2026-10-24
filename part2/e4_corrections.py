"""E4: boosted corrections on top of the level-calibrated developed prior, restricted to small candidate feature sets.
5-fold CV grouped by customer on emerging rows; per-line and pooled D2; stumps (2 leaves) with strong shrinkage."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
PE = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.02, num_leaves=2, min_data_in_leaf=300, feature_fraction=1.0, bagging_fraction=0.8, bagging_freq=1, lambda_l2=50.0, verbose=-1, num_threads=8, max_bin=32)
AGE = {"motor": "driver_age_band", "buildings": "policyholder_age_band", "contents": "policyholder_age_band"}
SETS = {"none": lambda l: [], "gender": lambda l: ["gender"], "gender+NB": lambda l: ["gender", "new_business"], "gender+NB+age": lambda l: ["gender", "new_business", AGE[l]],
        "gender+NB+age+urban+region": lambda l: ["gender", "new_business", AGE[l], "urban_density", "region"],
        "all small": lambda l: ["gender", "new_business", AGE[l], "urban_density", "region", "channel", "self_employed", "payment_method", "marital_status"]}
ROUNDS = (0, 20, 40, 80, 150, 300)
res = {s: {r: [] for r in ROUNDS} for s in SETS}; ys = []; per = {s: {} for s in SETS}
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devprior_{line}.parquet"), on="row_id")
    y, lfe = cap_target(em["y"].to_numpy(), 0.99); w = offset(em); grp = em["customer_id"].to_numpy(); ldev = em["lr_dev"].to_numpy(); ye = em["y"].to_numpy(); ys.append(ye)
    for s, f in SETS.items():
        cols = f(line); oof = {r: np.zeros(len(y)) for r in ROUNDS}
        X = to_pandas(em.select(["row_id"] + cols), ["row_id"]) if cols else None
        if X is not None: X = codes(X)
        for tri, vai in GroupKFold(5).split(em, y, grp):
            k = y[tri].sum() / (np.exp(ldev[tri]) * w[tri] / lfe).sum()   # level of the prior (capped target), set on the training folds
            init = np.log(w) + ldev - np.log(lfe) + np.log(k)
            if X is None:
                for r in ROUNDS: oof[r][vai] = np.exp(init[vai]) * lfe
                continue
            m = lgb.train({**PE, "seed": 0}, lgb.Dataset(X.iloc[tri], y[tri], init_score=init[tri]), max(ROUNDS))
            for r in ROUNDS: oof[r][vai] = np.exp(init[vai] + (m.predict(X.iloc[vai], raw_score=True, num_iteration=r) if r else 0)) * lfe
        per[s][line] = {r: round(d2(ye, oof[r]), 4) for r in ROUNDS}
        for r in ROUNDS: res[s][r].append(oof[r])
Y = np.concatenate(ys)
for s in SETS:
    print(f"{s:28s} pooled", {r: round(d2(Y, np.concatenate(res[s][r])), 4) for r in ROUNDS}); 
    for l in LINES: print(f"{'':28s}   {l:10s}", per[s][l])
