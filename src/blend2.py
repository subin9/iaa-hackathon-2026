"""Blend weights fitted on the mean D2 of both validation folds.

Weights are a softmax of free parameters (non-negative, summing to one),
optimized with Powell from equal weights. Also reports a leave-one-fold
check: weights fitted on one fold, scored on the other.

usage: blend2.py OUT_NAME MODEL [MODEL ...]
"""
import sys
import numpy as np, polars as pl
from scipy.optimize import minimize
from blend import frame, score


def fit(folds, models):
    obj = lambda t: -np.mean([score(f, models, np.exp(t) / np.exp(t).sum()) for f in folds])
    t = minimize(obj, np.zeros(len(models)), method="Powell", options={"xtol": 1e-2, "ftol": 1e-6}).x
    return np.exp(t) / np.exp(t).sum()


def main(out, models):
    F = {f: frame(models, f) for f in ("v2024", "v2023")}
    for f, df in F.items():
        print(f, {m: round(score(df, [m], [1]), 4) for m in models})
    for a, b in (("v2024", "v2023"), ("v2023", "v2024")):
        w = fit([F[a]], models)
        print(f"fit {a} score {b}: {score(F[b], models, w):.4f}", dict(zip(models, np.round(w, 2))))
    w = fit(list(F.values()), models)
    print("both:", dict(zip(models, np.round(w, 3))), {f: round(score(df, models, w), 4) for f, df in F.items()})
    te = frame(models, "test")
    pred = sum(te[m].to_numpy() * wi for m, wi in zip(models, w))
    te.select("row_id").with_columns(prediction=pl.Series(np.maximum(pred, 0))).write_csv(f"submissions/{out}.csv")
    print("wrote", out, "mean", pred.mean())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
