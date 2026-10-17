import sys; sys.path.insert(0, "src")
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, d2
P = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=int(sys.argv[1]), min_data_in_leaf=int(sys.argv[2]),
         feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, cat_smooth=50, min_data_per_group=500, verbose=-1, num_threads=16)
for line in LINES:
    df = load(line).filter(pl.col("split") == "train")
    tr, va = df.filter(pl.col("year") <= 2023), df.filter(pl.col("year") == 2024)
    X = to_pandas(tr); Xv = align_categories(X, to_pandas(va))
    y = tr["y"].to_numpy(); w = tr["exposure"].to_numpy()*tr["completion"].to_numpy(); base = np.log(y.sum()/w.sum())
    yv = va["y"].to_numpy(); wv = va["exposure"].to_numpy()*va["completion"].to_numpy()
    m = lgb.train(P, lgb.Dataset(X, y, init_score=np.log(w)+base), 1500)
    out = []
    for r in (50, 100, 200, 400, 700, 1000, 1500):
        p = np.exp(np.log(wv)+base+m.predict(Xv, raw_score=True, num_iteration=r))
        ks = {k: d2(yv, p*k) for k in (1.0, 1.2, 1.4, 1.6)}
        out.append(f"r{r}: " + " ".join(f"{k}:{v:.4f}" for k, v in ks.items()))
    print(line, "\n  " + "\n  ".join(out), flush=True)
