"""Large-loss split. Every model caps row targets at the 99% quantile of
positive costs and spreads the excess as a flat per-line multiplier. Here the
excess is modelled instead: a Poisson GBM gives the rate of rows above the cap
from the covariates, times the mean excess per large row. The saved column is
the expected excess only, so a blend can swap its flat load for it:
  pred = blend / load + excess

usage: large.py ROUNDS
"""
import sys, os
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, cap_target
from exp import codes
from run import FOLDS, line_trend

P = dict(objective="poisson", learning_rate=0.03, num_leaves=7, min_data_in_leaf=5000, feature_fraction=0.7,
         bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=int(os.environ.get("NT", 6)))


def main(rounds):
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            df = load(line)
            tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
            te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
            X = codes(to_pandas(tr)); Xt = codes(align_categories(to_pandas(tr), to_pandas(te))); Xt["year"] = last
            y = tr["y"].to_numpy()
            yc, load_f = cap_target(y, 0.99)
            big = (y > yc).astype(float)
            w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
            sev = (y - yc).sum() / big.sum()
            base = np.log(big.sum() / w.sum())
            m = lgb.train(P, lgb.Dataset(X, big, init_score=np.log(w) + base), rounds)
            scale = te["exposure"].to_numpy() * np.exp(line_trend(tr) * (ty - last))
            if fold != "test":
                scale = scale * te["completion"].to_numpy()
            ex = np.exp(base + m.predict(Xt, raw_score=True)) * sev * scale
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(ex), load=pl.lit(load_f)))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/large{rounds}_{fold}.parquet")
        print("large", fold, "sum excess", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]))
