"""Tweedie GLM (power 1.5, log link) per line, as a smooth model for the blend.

Numeric features are cut into quantile bins and every feature is one-hot
encoded, so the GLM fits a step function per factor. Like ag.py it models the
rate y / (exposure x completion) with weight (exposure x completion)^0.5,
which equals the offset fit for this power. Saved under the name "glm".
"""
import numpy as np, polars as pl
from sklearn.linear_model import TweedieRegressor
from sklearn.preprocessing import OneHotEncoder
from common import LINES, load, to_pandas, align_categories, cap_target
from run import FOLDS, line_trend

P = 1.5
BINS = 10


def design(X, edges=None):
    X = X.drop(columns=["year"]).copy()
    edges = edges if edges is not None else {
        c: np.unique(np.nanquantile(X[c].astype(float), np.linspace(0, 1, BINS + 1)[1:-1]))
        for c in X.columns if X[c].dtype.kind in "iuf"}
    for c, e in edges.items():
        v = X[c].astype(float).to_numpy()
        X[c] = np.where(np.isnan(v), -1, np.searchsorted(e, v)).astype(int).astype(str)
    return X.astype(str), edges


def main():
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            df = load(line)
            tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
            te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
            X = to_pandas(tr); Xt = align_categories(X, to_pandas(te))
            D, edges = design(X); Dt, _ = design(Xt, edges)
            enc = OneHotEncoder(handle_unknown="ignore", min_frequency=200)
            A = enc.fit_transform(D); At = enc.transform(Dt)
            y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
            w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
            m = TweedieRegressor(power=P, link="log", alpha=1e-4, max_iter=300).fit(A, y / w, sample_weight=w ** (2 - P))
            p = m.predict(At) * te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
            p = p * y.sum() * load_f / (m.predict(A) * w * load_f).sum()  # hold the training total
            if fold != "test":
                p = p * te["completion"].to_numpy()
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(p)))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/glm_{fold}.parquet")
        print("glm", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    main()
