"""Part 2 EDA 4: what changed. PSI of every shared feature between (a) developed 2024 and emerging 2023-24 and
(b) emerging train and emerging 2025 test, plus adversarial AUC of both pairs."""
import numpy as np, polars as pl, lightgbm as lgb, pandas as pd
from sklearn.metrics import roc_auc_score
pl.Config.set_tbl_rows(80); pl.Config.set_tbl_width_chars(200)
D = "data/part2/"
ID = ["row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "renewal_decision", "surname", "customer_since_year", "customer_service_contacts", "exposure"]

def table(mk, line, which):
    c = pl.read_parquet(f"{D}{mk}/customers.parquet"); a = pl.read_parquet(f"{D}{mk}/addresses.parquet")
    p = pl.concat([pl.read_parquet(f"{D}{mk}/policies_{line}.parquet").with_columns(split=pl.lit("train")),
                   pl.read_parquet(f"{D}{mk}/test_{line}.parquet").with_columns(split=pl.lit("test"))], how="diagonal_relaxed")
    return p.join(c, on="customer_id", how="left").join(a, on="address_id", how="left").with_columns(year=pl.col("period_start").dt.year())

def psi(a, b, bins=10):
    a, b = a.drop_nulls(), b.drop_nulls()
    if a.dtype.is_numeric() and a.n_unique() > 12:
        e = np.unique(np.quantile(a.to_numpy(), np.linspace(0, 1, bins + 1)[1:-1]))
        pa = np.bincount(np.searchsorted(e, a.to_numpy()), minlength=len(e) + 1) / len(a); pb = np.bincount(np.searchsorted(e, b.to_numpy()), minlength=len(e) + 1) / len(b)
    else:
        cats = sorted(set(a.cast(pl.Utf8).unique().to_list()) | set(b.cast(pl.Utf8).unique().to_list()))
        ca, cb = a.cast(pl.Utf8).value_counts(), b.cast(pl.Utf8).value_counts()
        da = dict(zip(ca[a.cast(pl.Utf8).name], ca["count"])) if False else dict(ca.iter_rows()); db = dict(cb.iter_rows())
        pa = np.array([da.get(k, 0) for k in cats]) / len(a); pb = np.array([db.get(k, 0) for k in cats]) / len(b)
    pa, pb = np.clip(pa, 1e-4, None), np.clip(pb, 1e-4, None)
    return float(((pa - pb) * np.log(pa / pb)).sum())

def adv(x, y, cols):
    X = pd.concat([x.select(cols).to_pandas(), y.select(cols).to_pandas()], ignore_index=True)
    for c in X.columns:
        if X[c].dtype == object or str(X[c].dtype) in ("string", "str", "bool", "boolean"): X[c] = X[c].astype("category")
    lab = np.r_[np.zeros(len(x)), np.ones(len(y))]
    idx = np.random.default_rng(0).permutation(len(X)); cut = int(0.7 * len(X)); tr, va = idx[:cut], idx[cut:]
    m = lgb.train(dict(objective="binary", learning_rate=0.1, num_leaves=15, min_data_in_leaf=100, verbose=-1, num_threads=8), lgb.Dataset(X.iloc[tr], lab[tr]), 150)
    imp = sorted(zip(m.feature_importance("gain"), cols), reverse=True)[:5]
    return round(roc_auc_score(lab[va], m.predict(X.iloc[va])), 3), [(c, int(g)) for g, c in imp]

for line in ("motor", "buildings", "contents"):
    dev = table("developed", line, None).filter((pl.col("year") == 2024)); em = table("emerging", line, None)
    etr, ete = em.filter(pl.col("split") == "train"), em.filter(pl.col("split") == "test")
    shared = [c for c in em.columns if c in dev.columns and c not in ID and c not in ("split", "year", "region", "branch_id")]
    rows = [dict(col=c, psi_dev_vs_em=round(psi(dev[c], em[c]), 3), psi_train_vs_test=round(psi(etr[c], ete[c]), 3)) for c in shared]
    print("\n=====", line); print(pl.DataFrame(rows).sort("psi_dev_vs_em", descending=True).head(25))
    num = [c for c in shared if em[c].dtype.is_numeric() or em[c].dtype in (pl.Boolean, pl.Utf8)]
    print("adversarial AUC developed-2024 vs emerging:", adv(dev, em, shared))
    print("adversarial AUC emerging train vs test   :", adv(etr, ete, shared + ["region"]))
