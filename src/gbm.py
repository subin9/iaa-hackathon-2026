"""LightGBM Tweedie per line, with exposure x completion offset and a year trend.

The model sees `year` as a feature. To project to a later year we score with
year set to the last training year and multiply by a log-linear trend fitted to
the model's own partial dependence on year, so mix changes do not leak into
the trend.
"""
import sys
import numpy as np
import lightgbm as lgb
import polars as pl
from common import LINES, load, to_pandas, align_categories, d2, cap_target

PARAMS = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.03,
              num_leaves=31, min_data_in_leaf=500, feature_fraction=0.7, bagging_fraction=0.8,
              bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50,
              min_data_per_group=500, verbose=-1, num_threads=16)


def fit(tr, rounds, cap_q=0.999, params=PARAMS, drop=()):
    X = to_pandas(tr, drop)
    y, load_factor = cap_target(tr["y"].to_numpy(), cap_q)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    base = np.log(y.sum() / w.sum())  # start at the mean rate so boosting only learns relativities
    m = lgb.train(params, lgb.Dataset(X, y, init_score=np.log(w) + base), rounds)
    # partial dependence on year -> trend slope
    S = X.sample(min(len(X), 100_000), random_state=0)
    years = sorted(tr["year"].unique().to_list())
    pd_ = []
    for yv in years:
        S2 = S.copy(); S2["year"] = yv
        pd_.append(np.log(np.exp(base + m.predict(S2, raw_score=True)).mean()))
    slope = np.polyfit(years, pd_, 1)[0] if len(years) > 1 else 0.0
    return dict(model=m, X=X, base=base, load=load_factor, slope=slope, last=max(years), pd=dict(zip(years, np.round(pd_, 4))))


def predict(f, te, target_year, drop=()):
    X = align_categories(f["X"], to_pandas(te, drop))
    X["year"] = f["last"]
    rate = np.exp(f["base"] + f["model"].predict(X, raw_score=True))
    return rate * te["exposure"].to_numpy() * f["load"] * np.exp(f["slope"] * (target_year - f["last"]))


def validate(rounds, cap_q=0.999, drop=(), folds=((2023, 2024), (2022, 2023))):
    res = {}
    for last, vy in folds:
        ys, ps = [], []
        for line in LINES:
            df = load(line).filter(pl.col("split") == "train")
            tr, va = df.filter(pl.col("year") <= last), df.filter(pl.col("year") == vy)
            f = fit(tr, rounds, cap_q, drop=drop)
            p = predict(f, va, vy, drop) * va["completion"].to_numpy()
            y = va["y"].to_numpy()
            print(f"  {vy} {line}: d2={d2(y, p):.4f} A/E={y.sum()/p.sum():.3f} slope={f['slope']:.4f} pd={f['pd']}", flush=True)
            ys.append(y); ps.append(p)
        res[vy] = d2(np.concatenate(ys), np.concatenate(ps))
        print(f"valid {vy}: pooled d2={res[vy]:.5f}", flush=True)
    return res


if __name__ == "__main__":
    validate(int(sys.argv[1]) if len(sys.argv) > 1 else 600)
