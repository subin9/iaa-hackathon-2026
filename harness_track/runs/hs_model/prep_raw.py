"""Cell (4) of the 2x2: modelling tables from the RAW emerging data with the minimum a naive pipeline would do.

No repairs (exposure as stored, sum_insured as stored, occupation as typed, nulls as delivered), no exclusions.
Target y = sum of (incurred_to_date - recoveries) over claims of the same policy_id whose loss_date falls inside the
row's period (repudiated = 0); claims that link to no row simply drop out. Cap at the 99th percentile of positive row
targets per line (the same modelling rule as the cleaned tables, so the data effect is not confounded by the cap).
Two completion variants are written as columns:
  completion        = 1.0            (naive: no IBNR adjustment)              -> tag raw_nocomp
  completion_d4      = the cleaned version's completion factor joined by row_id (isolates repairs from target construction)
                                                                               -> tag raw_comp
Leakage columns are renamed with the x_ prefix so train_hs.py's DROP lists apply identically to both data versions.
Output: runs/hs_model/raw_tables/{motor,buildings,contents}.parquet
"""
from __future__ import annotations
import numpy as np, polars as pl
from pathlib import Path
import argparse
ROOT = Path(__file__).resolve().parents[2]
_ap = argparse.ArgumentParser(); _ap.add_argument("--src", default=str(ROOT / "week2_data" / "emerging")); _ap.add_argument("--out", default="raw_tables"); _ap.add_argument("--fix-exposure", action="store_true", help="recompute exposure from the period dates (the single Week-1 repair), everything else as delivered")
_a = _ap.parse_args()
E = Path(_a.src); OUT = Path(__file__).resolve().parent / _a.out; OUT.mkdir(exist_ok=True)
VAL = pl.date(2024, 12, 31); MAXAGE = 760
RENAME = {"customer_since_year": "x_customer_since_year", "campaign_code": "x_campaign_code",
          "customer_service_contacts": "x_customer_service_contacts", "renewal_decision": "x_renewal_decision", "surname": "x_surname"}

claims = pl.read_parquet(E / "claims.parquet").with_columns(pl.col("loss_date").cast(pl.Date), pl.col("report_date").cast(pl.Date))
claims = claims.with_columns(pl.when(pl.col("status") == "repudiated").then(0.0).otherwise(pl.col("incurred_to_date") - pl.col("recoveries")).alias("net"),
                             (pl.col("report_date") - pl.col("loss_date")).dt.total_days().alias("lag"))
cust = pl.read_parquet(E / "customers.parquet"); addr = pl.read_parquet(E / "addresses.parquet")

def completion_curve(c: pl.DataFrame):
    """Reverse-time product-limit estimate of the cumulative cost-reported-by-age curve, from right-truncated claims."""
    c = c.filter(pl.col("lag") >= 0).with_columns(((VAL - pl.col("loss_date")).dt.total_days()).alias("age_at_val"))
    cap = c["net"].quantile(0.995) or 1.0
    c = c.with_columns(pl.col("net").clip(upper_bound=cap).alias("w"))
    lag = c["lag"].to_numpy(); w = c["w"].to_numpy(); age = c["age_at_val"].to_numpy()
    G = np.ones(MAXAGE + 1)
    # for each age a (descending), hazard of "reported at exactly a" among claims observable at age a (age_at_val >= a and lag >= a)
    for a in range(MAXAGE, 0, -1):
        risk = (age >= a) & (lag >= a)
        rep = risk & (lag == a)
        denom = w[risk].sum(); num = w[rep].sum()
        G[a - 1] = G[a] * (1 - (num / denom if denom > 0 else 0.0))
    return G  # G[a] = share of ultimate cost reported by age a

for line in ["motor", "buildings", "contents"]:
    c = claims.filter(pl.col("line") == line)
    G = completion_curve(c); H = np.concatenate([[0.0], np.cumsum(G)])
    parts = []
    for split, f in (("train", f"policies_{line}"), ("test", f"test_{line}")):
        p = pl.read_parquet(E / f"{f}.parquet").with_columns(pl.col("period_start").cast(pl.Date), pl.col("period_end").cast(pl.Date))
        p = p.join(cust, on="customer_id", how="left").join(addr, on="address_id", how="left")
        p = p.with_columns(pl.lit(split).alias("split"), pl.col("period_start").dt.year().alias("year"))
        if _a.fix_exposure:
            p = p.with_columns((((pl.col("period_end") - pl.col("period_start")).dt.total_days() + 1) / 365).round(4).alias("exposure"))
        if split == "train":
            j = p.select("row_id", "policy_id", "period_start", "period_end").join(c.select("policy_id", "loss_date", "net"), on="policy_id", how="inner")
            j = j.filter((pl.col("loss_date") >= pl.col("period_start")) & (pl.col("loss_date") <= pl.col("period_end")))
            y = j.group_by("row_id").agg(pl.col("net").sum().alias("y"))
            p = p.join(y, on="row_id", how="left").with_columns(pl.col("y").fill_null(0.0))
            lo = np.clip(p.select((VAL - pl.col("period_end")).dt.total_days()).to_series().to_numpy(), 0, MAXAGE - 1)
            hi = np.clip(p.select((VAL - pl.col("period_start")).dt.total_days()).to_series().to_numpy(), 0, MAXAGE - 1)
            comp = (H[hi + 1] - H[lo]) / (hi - lo + 1)
            p = p.with_columns(pl.Series("completion_curve", comp))
        else:
            p = p.with_columns(pl.lit(None, dtype=pl.Float64).alias("y"), pl.lit(1.0).alias("completion_curve"))
        p = p.with_columns(pl.lit(1.0).alias("completion"))
        parts.append(p)
    df = pl.concat(parts, how="diagonal_relaxed")
    ypos = df.filter(pl.col("y") > 0)["y"]; capv = ypos.quantile(0.99)
    df = df.with_columns(pl.when(pl.col("y").is_null()).then(None).otherwise(pl.min_horizontal(pl.col("y"), pl.lit(capv))).alias("y_cap"))
    d4 = pl.read_parquet(ROOT / f"runs/cycle_4/modelling_tables/{line}.parquet").select(pl.col("row_id").cast(pl.String), pl.col("completion").alias("completion_d4"))
    df = df.with_columns(pl.col("row_id").cast(pl.String)).drop("completion_curve").join(d4, on="row_id", how="left")
    df = df.rename({k: v for k, v in RENAME.items() if k in df.columns})
    df.write_parquet(OUT / f"{line}.parquet")
    tr = df.filter(pl.col("split") == "train")
    print(f"{line}: {df.shape}, train Σy {tr['y'].sum():,.0f}, exposure (as stored) {tr['exposure'].sum():,.1f}, cap {capv:,.0f}, "
          f"mean completion_d4 2023 {tr.filter(pl.col('year')==2023)['completion_d4'].mean():.3f} / 2024 {tr.filter(pl.col('year')==2024)['completion_d4'].mean():.3f}")
