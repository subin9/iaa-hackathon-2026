"""Experience rating on top of a blend (Poisson-gamma credibility).

A Poisson GBM per line gives every row its expected claim count from the
covariates. For a target row, N is the claim count and L the expected count
(times count completion) summed over all earlier-year rows sharing a key
(policy, customer across lines, or address across lines). The credibility
multiplier is (a + N) / (a + L): a policy that claimed more than its
covariates imply is riskier than they say. Each fold writes the multipliers
for its target rows to work/exprate_{fold}.parquet.

usage: exprate.py
"""
import os
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories
from exp import codes
from run import FOLDS

P = dict(objective="poisson", learning_rate=0.05, num_leaves=15, min_data_in_leaf=2000, feature_fraction=0.7,
         bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=int(os.environ.get("NT", 6)))
KEYS = ("policy_id", "customer_id", "address_id")


def positive_counts():
    """Claims with a positive net cost per row; repudiated and nil claims left out."""
    from prep import load_claims
    c = load_claims().filter(pl.col("net") > 0)
    rows = pl.concat([load(l).select("row_id", "policy_id", "period_start", "period_end") for l in LINES])
    m = c.join(rows, on="policy_id").filter(pl.col("loss_date").is_between(pl.col("period_start"), pl.col("period_end")))
    return m.group_by("row_id").agg(npos=pl.len())


def expected_counts(last, ty, pos=None):
    """Rows of all lines up to year last with observed and expected counts, plus target rows of year ty."""
    hist, targets = [], []
    for line in LINES:
        df = load(line)
        tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
        if pos is not None:
            tr = tr.join(pos, on="row_id", how="left").with_columns(n=pl.col("npos").fill_null(0)).drop("npos")
        X = codes(to_pandas(tr))
        w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
        n = tr["n"].to_numpy().astype(float)
        base = np.log(n.sum() / w.sum())
        # out of fold by policy, so a policy's own claims do not pull its expected count up
        grp = np.array([hash(p) % 5 for p in tr["policy_id"].to_numpy()])
        lam = np.empty(len(n))
        for k in range(5):
            t = grp != k
            m = lgb.train(P, lgb.Dataset(X[t], n[t], init_score=np.log(w[t]) + base), 200)
            lam[~t] = np.exp(base + m.predict(X[~t], raw_score=True)) * w[~t]
        hist.append(tr.select(*KEYS, "year", "n").with_columns(lam=pl.Series(lam)))
        te = df.filter(pl.col("split") == "test") if ty == 2025 else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
        targets.append(te.select("row_id", *KEYS))
    return pl.concat(hist, how="diagonal_relaxed"), pl.concat(targets)


def main():
    pos = positive_counts() if os.environ.get("EXP_POS") else None
    for fold, (last, ty) in FOLDS.items():
        hist, tg = expected_counts(last, ty, pos)
        out = tg.select("row_id")
        for k in KEYS:
            g = hist.group_by(k).agg(pl.col("n").sum().alias(f"N_{k}"), pl.col("lam").sum().alias(f"L_{k}"))
            out = out.join(tg.select("row_id", k).join(g, on=k, how="left").drop(k), on="row_id", how="left")
        out = out.fill_null(0)
        out.write_parquet(f"work/exprate{os.environ.get('EXP_TAG', '')}_{fold}.parquet")
        print(fold, out.select(pl.col("^[NL]_.*$").sum()).rows(), flush=True)


if __name__ == "__main__":
    main()
