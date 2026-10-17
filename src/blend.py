"""Score saved predictions per fold, fit blend weights on v2024, check on v2023,
and write the blended test submission.

usage: blend.py MODEL [MODEL ...]
"""
import sys, os, itertools
import numpy as np, polars as pl
from common import d2


def frame(models, fold):
    df = None
    for m in models:
        p = pl.read_parquet(f"work/preds/{m}_{fold}.parquet").rename({"pred": m})
        df = p if df is None else df.join(p.select("row_id", m), on="row_id")
    return df


def score(df, models, w):
    p = sum(df[m].to_numpy() * wi for m, wi in zip(models, w))
    return d2(df["y"].to_numpy(), p)


def main(models):
    folds = {f: frame(models, f) for f in ("v2024", "v2023")}
    for f, df in folds.items():
        print(f, {m: round(score(df, [m], [1]), 4) for m in models},
              "by line:", {l: {m: round(score(df.filter(pl.col("line") == l), [m], [1]), 4) for m in models} for l in ("motor", "buildings", "contents")})
    # grid over simplex weights in steps of 0.1
    grid = [w for w in itertools.product(np.arange(0, 1.01, 0.1), repeat=len(models)) if abs(sum(w) - 1) < 1e-9]
    best = max(grid, key=lambda w: score(folds["v2024"], models, w))
    print("best weights on v2024", dict(zip(models, np.round(best, 2))),
          "v2024", round(score(folds["v2024"], models, best), 4), "v2023", round(score(folds["v2023"], models, best), 4))
    te = frame(models, "test")
    pred = sum(te[m].to_numpy() * wi for m, wi in zip(models, best))
    os.makedirs("submissions", exist_ok=True)
    name = "submissions/blend_" + "_".join(models) + ".csv"
    sub = te.select("row_id").with_columns(prediction=pl.Series(np.maximum(pred, 0)))
    sub.write_csv(name)
    print("wrote", name, sub.shape, "mean", sub["prediction"].mean())


if __name__ == "__main__":
    main(sys.argv[1:])
