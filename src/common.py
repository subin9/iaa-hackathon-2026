import numpy as np
import pandas as pd
import polars as pl
from sklearn.metrics import d2_tweedie_score

LINES = ["motor", "buildings", "contents"]
DROP = ["row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end",
        "split", "y", "n", "ymax", "completion", "exposure",
        # in-period contacts track claims in training years but not in the 2025 test rows
        "customer_service_contacts",
        # data-quality flags, training-only or meaningless as risk factors
        "exposure_bad", "si_bad"]


def load(line):
    return pl.read_parquet(f"work/{line}.parquet")


def to_pandas(df, drop_extra=()):
    per_peril = [c for c in df.columns if c.split("_")[0] in ("y", "n", "compc", "compk") and c not in ("y", "n", "n_lines")]
    X = df.drop([c for c in DROP + per_peril + list(drop_extra) if c in df.columns]).to_pandas()
    for c in X.columns:
        if X[c].dtype == object or str(X[c].dtype) in ("string", "str") or X[c].dtype == bool:
            X[c] = X[c].astype("category")
    return X


def align_categories(X_tr, X_te):
    for c in X_tr.columns:
        if isinstance(X_tr[c].dtype, pd.CategoricalDtype):
            X_te[c] = pd.Categorical(X_te[c].astype(object), categories=X_tr[c].cat.categories)
    return X_te


def d2(y, p):
    return d2_tweedie_score(y, np.maximum(p, 1e-9), power=1.5)


def cap_target(y, q):
    """Cap row targets at quantile q of positive values, spread excess as a multiplier."""
    if q is None:
        return y, 1.0
    cap = np.quantile(y[y > 0], q)
    yc = np.minimum(y, cap)
    return yc, y.sum() / yc.sum()
