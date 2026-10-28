"""Shared helpers for the Part 2 experiments: table loading, feature sets, the offset, scoring."""
import sys, os
sys.path.insert(0, "src")
import numpy as np, polars as pl, pandas as pd
import common
from common import d2, cap_target, align_categories, to_pandas
from exp import codes

LINES = ["motor", "buildings", "contents"]
# columns that exist only in one market, or whose meaning differs, never go into a transferred model
MARKET = ["region", "gender", "self_employed", "branch_id", "campaign_code", "marketing_segment"]
HISTORY = ["pol_nclaims", "pol_cost", "pol_nclaims_1y", "cust_nclaims", "cust_cost", "cust_nclaims_1y", "tenure_years", "n_lines", "year"]
PREMIUM = ["written_premium", "premium_rate", "discount_applied"]


def load(line, market):
    return pl.read_parquet(f"work/p2/{'dev_' if market == 'dev' else ''}{line}.parquet")


TAG = os.environ.get("P2_TAG", "")                      # suffix of the prior files, e.g. "_nb"
KEEP = [c for c in os.environ.get("P2_KEEP", "").split(",") if c]  # columns the prior keeps although a list below drops them, e.g. new_business


def drop_cols(extra=(), premium=False, weather=False, lean=True):
    d = [c for c in list(MARKET) + list(HISTORY) if c not in KEEP] + list(extra)
    if lean:
        d += [c for c in common.LEAN if c not in KEEP]
    if not premium:
        d += PREMIUM
    d += [c for c in os.environ.get("P2_DROP", "").split(",") if c]   # extra columns to leave out of the prior, e.g. make_model
    if weather:  # keep the weather columns that LEAN would drop
        d = [c for c in d if c not in ("hail_days", "wind_exposure_index", "freezing_days", "dry_summer_index", "wildfire_index", "rainfall_mm", "mean_temperature_c")]
    return d


def features(tr, te, drop):
    """Category codes follow the training table, so a developed model scores emerging rows consistently."""
    X = to_pandas(tr, drop); Xt = align_categories(X, to_pandas(te, drop))
    return codes(X), codes(Xt)[X.columns]  # LightGBM reads columns by position, so the order must match the training table


def offset(df):
    return df["exposure"].to_numpy() * df["completion"].to_numpy()


def pooled_d2(parts):
    """parts: list of (y, pred) per line."""
    y = np.concatenate([p[0] for p in parts]); q = np.concatenate([p[1] for p in parts])
    return d2(y, q), d2(y, q * y.sum() / q.sum())
