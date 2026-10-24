"""E6: per-peril corrections on the per-peril developed prior. For each peril: level k_p (shrunk toward the line level), then stumps on
weather and segment candidate columns fitted on emerging data. 5-fold CV grouped by customer; reports per-peril deviance gain
(Tweedie 1.5 on capped peril cost, relative to level-only) at several round counts, then line and pooled D2."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from lib import *
PE = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.02, num_leaves=2, min_data_in_leaf=200, feature_fraction=1.0, bagging_fraction=0.8, bagging_freq=1, lambda_l2=50.0, verbose=-1, num_threads=8, max_bin=32)
WX = {"glass_hail": ["hail_days", "wind_exposure_index", "mean_temperature_c"], "storm": ["wind_exposure_index", "hail_days"], "escape_of_water": ["freezing_days", "mean_temperature_c"],
      "subsidence": ["dry_summer_index", "rainfall_mm"], "flood": ["rainfall_mm"], "fire": ["wildfire_index"]}
AGE = {"motor": "driver_age_band", "buildings": "policyholder_age_band", "contents": "policyholder_age_band"}
SEGS = {"none": [], "wx": None, "wx+seg": None}
ROUNDS = (0, 25, 50, 100, 200, 400)
dev15 = lambda y, mu: float(np.sum(4 * y * np.maximum(mu, 1e-9) ** -0.5 + 4 * np.maximum(mu, 1e-9) ** 0.5))
N0 = 300
tot = {m: {r: [] for r in ROUNDS} for m in ("wx", "wx+seg")}; ys = []; gain_rows = []
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil_{line}.parquet"), on="row_id")
    perils = sorted(c[4:] for c in em.columns if c.startswith("lrp_")); grp = em["customer_id"].to_numpy(); ye = em["y"].to_numpy(); ys.append(ye); expo = em["exposure"].to_numpy()
    folds = list(GroupKFold(5).split(em, ye, grp)); oof = {m: {r: np.zeros(len(ye)) for r in ROUNDS} for m in tot}
    for p in perils:
        y, lf = cap_target(em[f"y_{p}"].to_numpy(), 0.995); w = expo * em[f"compk_{p}"].to_numpy(); lrp = em[f"lrp_{p}"].to_numpy() - np.log(lf)
        prior = np.exp(lrp) * w
        for m, extra in (("wx", []), ("wx+seg", ["gender", "new_business", AGE[line]])):
            cols = WX.get(p, []) + extra
            X = codes(to_pandas(em.select(["row_id"] + cols), ["row_id"])) if cols else None
            per_r = {r: np.zeros(len(y)) for r in ROUNDS}
            for tri, vai in folds:
                kp = y[tri].sum() / prior[tri].sum(); n = int(em[f"n_{p}"].to_numpy()[tri].sum())
                init = np.log(prior) + np.log(kp)
                if X is None:
                    for r in ROUNDS: per_r[r][vai] = np.exp(init[vai])
                    continue
                mdl = lgb.train({**PE, "seed": 0}, lgb.Dataset(X.iloc[tri], y[tri], init_score=init[tri]), max(ROUNDS))
                for r in ROUNDS: per_r[r][vai] = np.exp(init[vai] + (mdl.predict(X.iloc[vai], raw_score=True, num_iteration=r) if r else 0))
            for r in ROUNDS: oof[m][r] += per_r[r] * lf
            if m == "wx+seg" or WX.get(p):
                base = dev15(y, per_r[0]); gain_rows.append((line, p, m, int(em[f"n_{p}"].sum()), {r: round((base - dev15(y, per_r[r])) / base * 100, 2) for r in ROUNDS if r}))
    for m in tot:
        for r in ROUNDS: tot[m][r].append(oof[m][r])
    print(line, {m: {r: round(d2(ye, oof[m][r]), 4) for r in (0, 50, 100, 200, 400)} for m in tot}, flush=True)
for g in gain_rows: print(g)
Y = np.concatenate(ys)
for m in tot: print("pooled", m, {r: round(d2(Y, np.concatenate(tot[m][r])), 4) for r in ROUNDS})
