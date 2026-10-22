"""Fit every model on each fold and on all training years, save predictions.

Folds: train <= 2023 score 2024, train <= 2022 score 2023. Validation
predictions are multiplied by the row completion so they compare with the
reported target. The full fit scores the 2025 test rows.

usage: run.py MODEL [MODEL ...]   models: tw po twx fs fsN (fs averaged over N seeds)
"""
import sys, os
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, cap_target
import common
from exp import codes
import fs
from prep import load_claims

FOLDS = {"v2024": (2023, 2024), "v2023": (2022, 2023), "test": (2024, 2025)}
GBM = dict(learning_rate=0.05, num_leaves=15, min_data_in_leaf=2000, feature_fraction=0.7,
           bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1,
           num_threads=int(os.environ.get("NT", 6)))
LEAN = common.LEAN + ["year"]
SPECS = {
    "tw": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.5}, rounds=150, cap=0.99),
    "po": dict(params={**GBM, "objective": "poisson"}, rounds=300, cap=0.995),
    # extra_trees and power 1.4 won the exp2 grids; seed averaging removes most of their noise
    "twx": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "extra_trees": True}, rounds=200, cap=0.99, seeds=5),
    # recent-years model: older years down-weighted by 0.6 per year, for time diversity in the blend
    "twxr": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "extra_trees": True}, rounds=200, cap=0.99, seeds=5, decay=0.6),
    # three-leaf trees (at most pairwise interactions) beat 15 leaves by about 0.0016 on both folds
    "tw3": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "num_leaves": 3}, rounds=600, cap=0.99, seeds=3),
    "po3": dict(params={**GBM, "objective": "poisson", "num_leaves": 3}, rounds=1100, cap=0.995, seeds=3),
    "twx3": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "extra_trees": True, "num_leaves": 3}, rounds=900, cap=0.99, seeds=5),
    # the same with 63 histogram bins, about 0.0005 better on two seed sets (all of it in v2023)
    "tw3b": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "num_leaves": 3, "max_bin": 63}, rounds=600, cap=0.99, seeds=3),
    "po3b": dict(params={**GBM, "objective": "poisson", "num_leaves": 3, "max_bin": 63}, rounds=1100, cap=0.995, seeds=3),
    "twx3b": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "extra_trees": True, "num_leaves": 3, "max_bin": 63}, rounds=900, cap=0.99, seeds=5),
    # lean versions without weather, sales, marketing noise and time columns: about 0.001
    # better on v2023 with v2024 flat, so mainly a different view for the blend
    "tw3l": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "num_leaves": 3}, rounds=800, cap=0.99, seeds=3, drop=LEAN),
    "po3l": dict(params={**GBM, "objective": "poisson", "num_leaves": 3}, rounds=1400, cap=0.995, seeds=3, drop=LEAN),
    "twx3l": dict(params={**GBM, "objective": "tweedie", "tweedie_variance_power": 1.4, "extra_trees": True, "num_leaves": 3}, rounds=1200, cap=0.99, seeds=5, drop=LEAN),
    "pox": dict(params={**GBM, "objective": "poisson", "extra_trees": True}, rounds=450, cap=0.99, seeds=5),
}


def line_trend(tr):
    """Log-linear trend of completion-adjusted cost per exposure over mature years."""
    g = tr.group_by("year").agg(
        c=(pl.col("completion") * pl.col("exposure")).sum() / pl.col("exposure").sum(),
        r=pl.col("y").sum() / (pl.col("exposure") * pl.col("completion")).sum()).filter(pl.col("c") > 0.97).sort("year")
    return np.polyfit(g["year"].to_numpy(), np.log(g["r"].to_numpy()), 1)[0]


def fit_predict_gbm(spec, tr, te, target_year, seed=0):
    drop = spec.get("drop", ())
    X = codes(to_pandas(tr, drop)); Xt = codes(align_categories(to_pandas(tr, drop), to_pandas(te, drop)))
    y, load_f = cap_target(tr["y"].to_numpy(), spec["cap"])
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    base = np.log(y.sum() / w.sum())
    sw = spec.get("decay", 1.0) ** (tr["year"].max() - tr["year"].to_numpy())
    m = lgb.train({**spec["params"], "seed": seed}, lgb.Dataset(X, y, weight=sw, init_score=np.log(w) + base), spec["rounds"])
    last = int(tr["year"].max())
    if "year" in Xt: Xt["year"] = last
    g = line_trend(tr)
    return np.exp(base + m.predict(Xt, raw_score=True)) * te["exposure"].to_numpy() * load_f * np.exp(g * (target_year - last))


def main(models):
    claims = load_claims()
    os.makedirs("work/preds", exist_ok=True)
    for name in models:
        for fold, (last, ty) in FOLDS.items():
            parts = []
            for line in LINES:
                df = load(line)
                tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
                te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
                if name.startswith("fs"):
                    seeds = int(name[2:] or 1)
                    p = sum(fs.predict(fs.fit_line(line, tr, claims, seed=s), te, ty) for s in range(seeds)) / seeds
                else:
                    seeds = SPECS[name].get("seeds", 1)
                    p = sum(fit_predict_gbm(SPECS[name], tr, te, ty, seed=s) for s in range(seeds)) / seeds
                if fold != "test":
                    p = p * te["completion"].to_numpy()
                parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(p)))
            out = pl.concat(parts)
            out.write_parquet(f"work/preds/{name}{os.environ.get('TAG', '')}_{fold}.parquet")
            print(name, fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
