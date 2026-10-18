"""CatBoost Tweedie 1.5 per line with the log(exposure x completion) offset as baseline.

Categoricals go in natively (ordered target statistics), which gives the blend
a different view from the LightGBM code-based splits.

Runs in .venv-ag:
  cb.py scan      pooled D2 on both validation folds at checkpoints up to MAX_IT
  cb.py ITER      fit all folds at ITER iterations, save as "cb"
"""
import sys, os
import numpy as np, polars as pl
from catboost import CatBoostRegressor, Pool
from common import LINES, load, to_pandas, align_categories, cap_target, d2
from run import FOLDS, line_trend

MAX_IT = 1500
PARAMS = dict(loss_function="Tweedie:variance_power=1.5", learning_rate=float(os.environ.get("CB_LR", 0.05)), depth=int(os.environ.get("CB_DEPTH", 6)), l2_leaf_reg=10,
              min_data_in_leaf=500, thread_count=int(os.environ.get("NT", 6)), verbose=0, allow_writing_files=False)


def data(line, last, ty, fold):
    df = load(line)
    tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
    te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
    X = to_pandas(tr); Xt = align_categories(X, to_pandas(te)); Xt["year"] = last
    cats = [c for c in X.columns if str(X[c].dtype) == "category"]
    for c in cats:
        X[c] = X[c].astype(str); Xt[c] = Xt[c].astype(str)
    return tr, te, X, Xt, cats


def fit(line, last, ty, fold, iters, seed=0):
    tr, te, X, Xt, cats = data(line, last, ty, fold)
    y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    base = np.log(y.sum() / w.sum())
    m = CatBoostRegressor(iterations=iters, random_seed=seed, **PARAMS)
    m.fit(Pool(X, y, cat_features=cats, baseline=np.log(w) + base))
    scale = te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
    if fold != "test":
        scale = scale * te["completion"].to_numpy()
    pt = Pool(Xt, cat_features=cats)
    return te, m, pt, base, scale


def scan():
    for fold in ("v2024", "v2023"):
        last, ty = FOLDS[fold]
        ys, ps = [], {}
        for line in LINES:
            te, m, pt, base, scale = fit(line, last, ty, fold, MAX_IT)
            ys.append(te["y"].to_numpy())
            for i, raw in enumerate(m.staged_predict(pt, prediction_type="RawFormulaVal", eval_period=100)):
                ps.setdefault((i + 1) * 100, []).append(np.exp(raw + base) * scale)
        Y = np.concatenate(ys)
        print(fold, {k: round(d2(Y, np.concatenate(v)), 4) for k, v in ps.items()}, flush=True)


def main(iters, seeds=3):
    os.makedirs("work/preds", exist_ok=True)
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            acc = 0
            for s in range(seeds):
                te, m, pt, base, scale = fit(line, last, ty, fold, iters, seed=s)
                acc = acc + np.exp(m.predict(pt, prediction_type="RawFormulaVal") + base) * scale / seeds
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(acc)))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/{os.environ.get('CB_NAME', 'cb')}_{fold}.parquet")
        print("cb", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    scan() if sys.argv[1] == "scan" else main(int(sys.argv[1]))
