"""One LightGBM Tweedie model over all three lines, line as a feature.

Cap, load, base level and trend stay per line; the trees are shared, so
customer and address effects are learnt from all lines at once.
Saved as "pool" (5 seeds).

usage: pool.py
"""
import os
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, cap_target
from exp import BASE, codes
from run import FOLDS, line_trend

P = {**BASE, "extra_trees": True, "tweedie_variance_power": 1.4, "num_threads": int(os.environ.get("NT", 6))}
ROUNDS, SEEDS = 500, 5


def main():
    df = pl.concat([load(l).with_columns(line=pl.lit(l)) for l in LINES], how="diagonal_relaxed")
    for fold, (last, ty) in FOLDS.items():
        tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
        te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
        X = codes(to_pandas(tr)); Xt = codes(align_categories(to_pandas(tr), to_pandas(te))); Xt["year"] = last
        lt, lv = tr["line"].to_numpy(), te["line"].to_numpy()
        w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
        y = tr["y"].to_numpy().astype(float)
        base, scale = np.zeros(len(tr)), te["exposure"].to_numpy().astype(float)
        if fold != "test":
            scale = scale * te["completion"].to_numpy()
        for l in LINES:
            s, v = lt == l, lv == l
            y[s], load_f = cap_target(y[s], 0.99)
            b = np.log(y[s].sum() / w[s].sum())
            base[s] = b
            scale[v] *= np.exp(b) * load_f * np.exp(line_trend(tr.filter(pl.col("line") == l)) * (ty - last))
        p = 0
        for seed in range(SEEDS):
            m = lgb.train({**P, "seed": seed}, lgb.Dataset(X, y, init_score=np.log(w) + base), ROUNDS)
            p = p + np.exp(m.predict(Xt, raw_score=True)) * scale / SEEDS
        out = te.select("row_id", "y", "exposure", "line").with_columns(pred=pl.Series(p))
        out.write_parquet(f"work/preds/pool_{fold}.parquet")
        print("pool", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    main()
