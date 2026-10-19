"""LightGBM per peril, summed to the row prediction. Saved as "gbmp".

Each peril gets its own Tweedie model on its capped cost with the offset
log(exposure x peril completion), the same decomposition as tabm_peril.py.
The line trend and the line rounds are shared across perils.

usage: gbm_peril.py ROUNDS [SEEDS]
"""
import sys, os
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, cap_target
from exp import codes
from run import FOLDS, GBM, line_trend

PARAMS = {**GBM, "objective": "tweedie", "tweedie_variance_power": float(os.environ.get("GP_P", 1.4)), "extra_trees": True}


def predict(tr, te, ty, fold, rounds, seeds):
    X = codes(to_pandas(tr)); Xt = codes(align_categories(to_pandas(tr), to_pandas(te)))
    last = int(tr["year"].max()); Xt["year"] = last
    scale = te["exposure"].to_numpy() * np.exp(line_trend(tr) * (ty - last))
    total = 0
    for p in sorted(c[2:] for c in tr.columns if c.startswith("y_")):
        y, load_f = cap_target(tr[f"y_{p}"].to_numpy(), 0.995)
        w = np.maximum(tr["exposure"].to_numpy() * tr[f"compk_{p}"].to_numpy(), 1e-6)
        base = np.log(y.sum() / w.sum())
        ds = lgb.Dataset(X, y, init_score=np.log(w) + base)
        raw = sum(lgb.train({**PARAMS, "seed": s}, ds, rounds).predict(Xt, raw_score=True) for s in range(seeds)) / seeds
        comp = 1.0 if fold == "test" else te[f"compk_{p}"].to_numpy()
        total = total + np.exp(base + raw) * load_f * comp
    return total * scale


def main(rounds, seeds):
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            df = load(line)
            tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
            te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(predict(tr, te, ty, fold, rounds, seeds))))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/{os.environ.get('GP_NAME', 'gbmp')}_{fold}.parquet")
        print("gbmp", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 3)
