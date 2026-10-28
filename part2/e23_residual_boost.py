"""E23: boost the emerging residuals. Inside each fold, a small Tweedie LightGBM is trained on the emerging training rows with the pipeline's own fitted
values as offset, on every emerging column (gender, region, the claim history and the filled fields included), so it can pick up what the transferred prior
and the screened GLM corrections miss, including interactions. Its multiplier is renormalised to keep the pipeline's training total.
Same folds as e21/e22 on the cleaned files, v10's model as the pipeline, paired bootstrap by customer; the rounds are swept on one fit.
usage: e23_residual_boost.py [premium] [whitelist]   (premium: also give it the written premium; whitelist: only the rating and history columns in WL)"""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
import model2
from e22_cleaned_round2 import prior, dev, C, BASE

PREM = "premium" in sys.argv[1:]
ROUNDS = (0, 25, 50, 100, 200, 400)
PARAMS = {name: dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.02, num_leaves=l, min_data_in_leaf=m, feature_fraction=0.7,
                     bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=16, seed=0)
          for name, l, m in (("leaves 3, min leaf 300", 3, 300), ("leaves 7, min leaf 500", 7, 500), ("leaves 3, min leaf 1500", 3, 1500))}
SKIP = ["year", "exposure_bad", "si_bad", "customer_since_year", "customer_service_contacts"] + ([] if PREM else ["written_premium", "premium_rate", "discount_applied"])


# columns with an insurance reason to move motor cost that the prior cannot see or sees only through the developed market
WL = ["marital_status", "ncb_years", "pol_cost", "pol_nclaims", "cust_cost", "cust_nclaims", "licence_points", "prior_claims_5y", "missed_payments_12m",
      "household_size", "occupation", "gender", "driver_age_band", "region", "urban_density"] + (["written_premium", "premium_rate"] if PREM else [])


def frame(df):
    if "whitelist" in sys.argv[1:]: return df.select([c for c in WL if c in df.columns])
    return df.select([c for c in df.columns if not c.startswith(("lrp_", "y_", "n_", "compk_", "compc_")) or c == "n_lines"])


ys, cs, base, boosted = [], [], [], {(p, r): [] for p in PARAMS for r in ROUNDS}
for line in LINES:
    em = pl.read_parquet(f"{C}/{line}.parquet").filter(pl.col("split") == "train").join(prior(C, BASE, line), on="row_id").sort("row_id")
    y = em["y"].to_numpy(); o = np.zeros(len(y)); ob = {k: np.zeros(len(y)) for k in boosted}
    for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
        tr, va = em[tri], em[vai]
        pt = model2.pipeline(tr, tr, short=model2.SHORT[line], score_is_train=True)
        pv = model2.pipeline(tr, va, short=model2.SHORT[line], score_is_train=True)
        o[vai] = pv
        X, Xv = features(frame(tr), frame(va), SKIP)
        yc, lf = cap_target(y[tri], 0.995)
        for pname, P in PARAMS.items():
            m = lgb.train(P, lgb.Dataset(X, yc, init_score=np.log(pt) - np.log(lf)), max(ROUNDS))
            for r in ROUNDS:
                ft = m.predict(X, raw_score=True, num_iteration=r) if r else np.zeros(len(X)); fv = m.predict(Xv, raw_score=True, num_iteration=r) if r else np.zeros(len(Xv))
                k = (pt * np.exp(ft)).sum() / pt.sum()
                ob[(pname, r)][vai] = pv * np.exp(fv) / k
    ys.append(y); cs.append(em["customer_id"].to_numpy()); base.append(o)
    for k in boosted: boosted[k].append(ob[k])
    print(line, "pipeline", round(d2(y, o), 5), {f"{p[:9]} r{r}": round(d2(y, ob[(p, r)]), 5) for p in PARAMS for r in ROUNDS if r}, flush=True)

Y, A, G = np.concatenate(ys), np.concatenate(base), np.concatenate(cs)
u, g = np.unique(G, return_inverse=True); dA = np.bincount(g, dev(Y, A)); d0 = np.bincount(g, dev(Y, np.full(len(Y), Y.mean())))
print(f"{'v10 model':36s} D2 {1 - dA.sum() / d0.sum():.5f}")
for (p, r), parts in list(boosted.items()) + [((p + ", motor only", r), [parts[0]] + base[1:]) for (p, r), parts in boosted.items()]:
    if not r: continue
    B = np.concatenate(parts); dB = np.bincount(g, dev(Y, B)); rng = np.random.default_rng(0)
    diff = np.array([(dA[i].sum() - dB[i].sum()) / d0[i].sum() for i in (rng.integers(0, len(u), len(u)) for _ in range(2000))])
    print(f"{p + ', rounds ' + str(r):48s} D2 {1 - dB.sum() / d0.sum():.5f}  gain {(dA.sum() - dB.sum()) / d0.sum():+.5f}  sd {diff.std():.5f}  P(gain>0) {(diff > 0).mean():.3f}", flush=True)
