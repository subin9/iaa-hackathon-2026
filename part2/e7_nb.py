"""E7: new-business effect after the prior. A/E of the prior on new-business rows vs renewal rows, by line and peril, emerging and developed
(developed: in-sample prediction of the same lean model, trees are shallow so over-fit is small)."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from lib import *
PD = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.05, num_leaves=3, min_data_in_leaf=2000, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
for line in LINES:
    dev = load(line, "dev").filter(pl.col("split") == "train")
    X, _ = features(dev, dev.head(5), drop_cols())
    y, lf = cap_target(dev["y"].to_numpy(), 0.99); w = offset(dev); b = np.log(y.sum() / w.sum())
    mu = np.exp(lgb.train({**PD, "seed": 0}, lgb.Dataset(X, y, init_score=np.log(w) + b), 800).predict(X, raw_score=True) + b) * w * lf
    nb = dev["new_business"].to_numpy(); yy = dev["y"].to_numpy(); r = np.sqrt(((yy - mu) ** 2)[nb].sum())
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devprior_{line}.parquet"), on="row_id")
    m2 = np.exp(em["lr_dev"].to_numpy()) * offset(em); k = em["y"].sum() / m2.sum(); m2 = m2 * k
    nbe = em["new_business"].to_numpy(); ye = em["y"].to_numpy(); se = np.sqrt(((ye - m2) ** 2)[nbe].sum())
    ch = em["channel"].to_numpy()
    print(f"{line:9s} dev  NB A/E {yy[nb].sum() / mu[nb].sum():.3f} (z {(yy[nb].sum() - mu[nb].sum()) / r:+.1f}, n={int(dev['n'].to_numpy()[nb].sum())}) | renewal A/E {yy[~nb].sum() / mu[~nb].sum():.3f}")
    print(f"{'':9s} em   NB A/E {ye[nbe].sum() / m2[nbe].sum():.3f} (z {(ye[nbe].sum() - m2[nbe].sum()) / se:+.1f}, n={int(em['n'].to_numpy()[nbe].sum())}) | renewal A/E {ye[~nbe].sum() / m2[~nbe].sum():.3f}")
    for c in ("broker", "direct", "comparison_site"):
        k_ = ch == c; print(f"{'':9s} em   channel {c:16s} A/E {ye[k_].sum() / m2[k_].sum():.3f} n={int(em['n'].to_numpy()[k_].sum())}  NB-only A/E {ye[k_ & nbe].sum() / max(m2[k_ & nbe].sum(), 1e-9):.3f} n={int(em['n'].to_numpy()[k_ & nbe].sum())}")
