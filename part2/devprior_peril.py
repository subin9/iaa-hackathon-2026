"""Per-peril developed-market prior: one shallow lean LightGBM per peril (Tweedie 1.4, capped cost, offset exposure x peril completion)
trained on all developed rows, scoring every emerging row. Writes work/p2/devperil_{line}.parquet: row_id and lrp_{peril} = log ultimate
cost rate per exposure year (including the cap load), 3 seeds averaged in log space."""
import sys, os; sys.path.insert(0, "part2")
import numpy as np, polars as pl, pandas as pd, lightgbm as lgb
from lib import *
PD = dict(objective="tweedie", tweedie_variance_power=1.4, learning_rate=0.05, num_leaves=3, min_data_in_leaf=2000, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 600
WEATHER_PERILS = {"glass_hail", "storm", "subsidence"}  # these perils see the weather columns when P2_WX=1 (the other weather perils lost deviance in emerging CV, see e9)
WX = os.environ.get("P2_WX") == "1"
VARIANT = os.environ.get("P2_VARIANT", "")   # "": Tweedie 1.4 | "poisson" | "extra": extra-trees Tweedie
if VARIANT == "poisson": PD = {**PD, "objective": "poisson"}; ROUNDS = int(ROUNDS * 1.8)
if VARIANT == "extra": PD = {**PD, "extra_trees": True}; ROUNDS = int(ROUNDS * 1.5)
# experiment knobs (e17): tree size, Tweedie power, and covariate-shift weights that make the developed rows look like the emerging ones
PD = {**PD, "num_leaves": int(os.environ.get("P2_LEAVES", PD["num_leaves"]))}
if os.environ.get("P2_POWER"): PD = {**PD, "tweedie_variance_power": float(os.environ["P2_POWER"])}
CSW = os.environ.get("P2_CSW") == "1"


def shift_weights(X, Xe):
    """Density ratio emerging / developed from a classifier on the prior's own columns, clipped at 20 and normalised to mean 1 on the developed rows."""
    Z = pd.concat([X, Xe], ignore_index=True); t = np.r_[np.zeros(len(X)), np.ones(len(Xe))]
    clf = lgb.train(dict(objective="binary", learning_rate=0.05, num_leaves=15, min_data_in_leaf=500, verbose=-1, num_threads=PD["num_threads"], seed=0), lgb.Dataset(Z, t), 300)
    q = np.clip(clf.predict(X), 1e-4, 1 - 1e-4); r = np.minimum(q / (1 - q) * len(X) / len(Xe), 20.0)
    print("shift weights: effective share of developed rows", round(float(r.sum() ** 2 / (r ** 2).sum() / len(r)), 3), flush=True)
    return r / r.mean()

for line in (os.environ.get("P2_ONLY", "").split(",") if os.environ.get("P2_ONLY") else LINES):
    dev = load(line, "dev").filter(pl.col("split") == "train"); em = load(line, "em")
    X0, Xe0 = features(dev, em, drop_cols())
    X1, Xe1 = features(dev, em, drop_cols(weather=True)) if WX else (X0, Xe0)
    out = {"row_id": em["row_id"]}; sw = shift_weights(X0, Xe0) if CSW else None
    for p in sorted(c[2:] for c in dev.columns if c.startswith("y_")):
        X, Xe = (X1, Xe1) if p in WEATHER_PERILS else (X0, Xe0)
        y, lf = cap_target(dev[f"y_{p}"].to_numpy(), 0.995)
        w = np.maximum(dev["exposure"].to_numpy() * dev[f"compk_{p}"].to_numpy(), 1e-6); b = np.log(y.sum() / w.sum())
        raw = np.mean([lgb.train({**PD, "seed": s}, lgb.Dataset(X, y, weight=sw, init_score=np.log(w) + b), ROUNDS).predict(Xe, raw_score=True) for s in range(3)], 0)
        out[f"lrp_{p}"] = raw + b + np.log(lf)
        print(line, p, "mean dev rate on emerging", round(float(np.exp(out[f"lrp_{p}"]).mean()), 1), flush=True)
    pl.DataFrame(out).write_parquet(f"work/p2/devperil{TAG}_{line}.parquet")
