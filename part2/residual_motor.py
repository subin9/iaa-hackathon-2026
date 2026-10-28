"""Motor residual booster (e23): a small Tweedie LightGBM on the motor training rows with the pipeline's fitted values as offset, on the rating, history and
premium columns of e23's whitelist (3 leaves, 1500 rows per leaf, 50 rounds at 0.02). Its multiplier, renormalised to the training total, scales the motor
rows of a fit_final.py output. Run from the tree that holds the tables.
usage: residual_motor.py BASE.parquet OUT.csv --tag _tm_avg"""
import sys, argparse; sys.path.insert(0, "part2")
import numpy as np, polars as pl, lightgbm as lgb
from lib import *
import model2, submission

WL = ["marital_status", "ncb_years", "pol_cost", "pol_nclaims", "cust_cost", "cust_nclaims", "licence_points", "prior_claims_5y", "missed_payments_12m",
      "household_size", "occupation", "gender", "driver_age_band", "region", "urban_density", "written_premium", "premium_rate"]
P = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.02, num_leaves=3, min_data_in_leaf=1500, feature_fraction=0.7, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=8)
ap = argparse.ArgumentParser(); ap.add_argument("base"); ap.add_argument("out"); ap.add_argument("--tag", default="_tm_avg"); a = ap.parse_args()

em = load("motor", "em").join(pl.read_parquet(f"work/p2/devperil{a.tag}_motor.parquet"), on="row_id")
tr, te = em.filter(pl.col("split") == "train"), em.filter(pl.col("split") == "test")
pt = model2.pipeline(tr, tr, short=model2.SHORT["motor"], score_is_train=True)
X, Xt = features(tr.select(WL), te.select(WL), []); yc, lf = cap_target(tr["y"].to_numpy(), 0.995)
ft, fx = np.zeros(len(X)), np.zeros(len(Xt))
for s in range(3):   # three seeds averaged in log space, as the priors
    m = lgb.train({**P, "seed": s}, lgb.Dataset(X, yc, init_score=np.log(pt) - np.log(lf)), 50)
    ft += m.predict(X, raw_score=True) / 3; fx += m.predict(Xt, raw_score=True) / 3
k = (pt * np.exp(ft)).sum() / pt.sum(); mult = np.exp(fx) / k
print("multiplier on the 2025 motor rows: p1, p50, p99", np.round(np.quantile(mult, [0.01, 0.5, 0.99]), 3),
      "| mean NB", round(float(mult[te["new_business"].to_numpy() == 1].mean()), 4), "renewal", round(float(mult[te["new_business"].to_numpy() == 0].mean()), 4))
base = pl.read_parquet(a.base)
f = te.select("row_id").with_columns(m=pl.Series(mult))
out = base.join(f, on="row_id", how="left").with_columns(prediction=pl.col("prediction") * pl.col("m").fill_null(1.0)).drop("m")
out.write_parquet(a.out.replace(".csv", ".parquet")); submission.write(out.select("row_id", "prediction"), a.out)
