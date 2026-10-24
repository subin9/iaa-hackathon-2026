"""Headline validation numbers for the report: the ladder from "port Part 1 unchanged" to the final pipeline, 5-fold CV grouped by customer on the
emerging 2023-24 rows, scored with the pooled Tweedie D2 (power 1.5) on reported cost (prediction x completion). Writes work/p2/report_numbers.json."""
import sys, json; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
import model2
TAGP = "_v_avg"
P_EM = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.03, num_leaves=3, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
steps = {k: [] for k in ("A constant rate per line", "B emerging-data model only (LightGBM)", "C Part 1 prior ported unchanged", "D prior, one level per line", "E prior, shrunk peril levels", "F final: E + screened corrections")}
ys = []; per = {k: {} for k in steps}; drop_em = [c for c in drop_cols(premium=True) if c not in ("region", "gender", "self_employed")]
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil{TAGP}_{line}.parquet"), on="row_id")
    ye = em["y"].to_numpy(); ys.append(ye); grp = em["customer_id"].to_numpy(); w = offset(em); folds = list(GroupKFold(5).split(em, ye, grp))
    out = {k: np.zeros(len(ye)) for k in steps}
    perils = model2.peril_cols(em)
    out["C Part 1 prior ported unchanged"] = sum(np.exp(em[f"lrp_{p}"].to_numpy()) * em["exposure"].to_numpy() * em[f"compk_{p}"].to_numpy() for p in perils)
    em0 = load(line, "em").filter(pl.col("split") == "train")   # no prior columns: model B must not see the developed market
    XE, _ = features(em0, em0.head(5), drop_em); y, lfe = cap_target(ye, 0.99)
    for tri, vai in folds:
        out["A constant rate per line"][vai] = ye[tri].sum() / w[tri].sum() * w[vai]
        b0 = np.log(y[tri].sum() / w[tri].sum()); m = lgb.train({**P_EM, "seed": 0}, lgb.Dataset(XE.iloc[tri], y[tri], init_score=np.log(w[tri]) + b0), 100)
        out["B emerging-data model only (LightGBM)"][vai] = np.exp(m.predict(XE.iloc[vai], raw_score=True) + b0) * w[vai] * lfe
        out["D prior, one level per line"][vai] = model2.pipeline(em[tri], em[vai], n0_level=1e12, short=[], score_is_train=True)
        out["E prior, shrunk peril levels"][vai] = model2.pipeline(em[tri], em[vai], short=[], score_is_train=True)
        out["F final: E + screened corrections"][vai] = model2.pipeline(em[tri], em[vai], short=model2.SHORT[line], score_is_train=True)
    for k in steps: steps[k].append(out[k]); per[k][line] = round(d2(ye, out[k]), 4)
Y = np.concatenate(ys); res = {k: {"pooled": round(d2(Y, np.concatenate(v)), 4), **per[k]} for k, v in steps.items()}
for k, v in res.items(): print(f"{k:42s}", v)
json.dump(res, open("work/p2/report_numbers.json", "w"), indent=1)
