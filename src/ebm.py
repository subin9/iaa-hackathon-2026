"""Explainable Boosting Machine (GA2M) with the Tweedie 1.5 objective, per line.

The offset log(exposure x completion) + base rate goes in as init_score.
Saved under the name "ebm".

Runs in .venv-ag:
  ebm.py scan    both validation folds, pooled D2
  ebm.py fit     all folds, save as "ebm"
"""
import sys, os, time
import numpy as np, polars as pl
from interpret.glassbox import ExplainableBoostingRegressor
from common import LINES, load, to_pandas, align_categories, cap_target, d2
from run import FOLDS, line_trend

NT = int(os.environ.get("NT", 6))


def fit_line(line, last, ty, fold):
    df = load(line)
    tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
    te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
    X = to_pandas(tr).drop(columns=["year"]); Xt = align_categories(X, to_pandas(te).drop(columns=["year"]))
    y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    base = np.log(y.sum() / w.sum())
    m = ExplainableBoostingRegressor(objective="tweedie_deviance:variance_power=1.5", outer_bags=int(os.environ.get("EBM_BAGS", 4)), inner_bags=0,
                                     interactions=int(os.environ.get("EBM_INT", 10)), learning_rate=0.02, min_samples_leaf=500, max_bins=64,
                                     n_jobs=NT, random_state=int(os.environ.get("EBM_SEED", 0)))
    m.fit(X, y, init_score=np.log(w) + base)
    scale = te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
    if fold != "test":
        scale = scale * te["completion"].to_numpy()
    p = m.predict(Xt, init_score=np.full(len(Xt), base)) * scale  # predict returns the mean, link already inverted
    return te, p


def run(folds, save):
    for fold in folds:
        last, ty = FOLDS[fold]
        parts = []
        for line in LINES:
            t = time.time()
            te, p = fit_line(line, last, ty, fold)
            print(fold, line, f"{time.time() - t:.0f}s", "d2", round(d2(te["y"].to_numpy(), p), 4) if fold != "test" else "", flush=True)
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(p)))
        out = pl.concat(parts)
        if fold != "test":
            print(fold, "pooled d2", round(d2(out["y"].to_numpy(), out["pred"].to_numpy()), 4), flush=True)
        if save:
            out.write_parquet(f"work/preds/{os.environ.get('EBM_NAME', 'ebm')}_{fold}.parquet")


if __name__ == "__main__":
    run(("v2024", "v2023"), False) if sys.argv[1] == "scan" else run(tuple(FOLDS), True)
