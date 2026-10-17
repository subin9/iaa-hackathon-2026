"""Extra history features, written to work/feats_{line}.parquet keyed by row_id.

All counts use claims reported before the row's period_start, as in prep.history.
- hist_years: how much claim history exists before the row (the data starts in 2021),
  and per-year rates of the policy and customer counts, so a 2025 row with four
  years of history reads like a 2022 row with one.
- addr_*: claims at the same address under any policy, and under other customers.
- cust_n_{motor,buildings,contents}: the customer's prior claims by line.
"""
import polars as pl
from prep import D, LINES, load_claims

START = pl.date(2021, 1, 1)


def policy_map():
    return pl.concat([pl.read_parquet(D + f"{f}_{l}.parquet", columns=["policy_id", "customer_id", "address_id"])
                      for f in ("policies", "test") for l in LINES]).unique("policy_id")


def build(line, claims, pmap):
    rows = pl.read_parquet(f"work/{line}.parquet", columns=["row_id", "customer_id", "address_id", "period_start",
                                                            "pol_nclaims", "cust_nclaims", "pol_cost", "cust_cost"])
    c = claims.join(pmap, on="policy_id").select("customer_id", "address_id", "line", "report_date", "net")
    hy = ((pl.col("period_start") - START).dt.total_days() / 365.25).clip(lower_bound=0.25)
    out = rows.select("row_id", hist_years=hy)
    j = rows.select("row_id", "address_id", "customer_id", "period_start").join(
        c.rename({"customer_id": "c_cust"}), on="address_id")
    j = j.filter(pl.col("report_date") < pl.col("period_start"))
    g = j.group_by("row_id").agg(
        addr_nclaims=pl.len(), addr_cost=pl.col("net").sum(),
        addr_nclaims_other=(pl.col("c_cust") != pl.col("customer_id")).sum())
    out = out.join(g, on="row_id", how="left")
    k = rows.select("row_id", "customer_id", "period_start").join(c.select("customer_id", "line", "report_date"), on="customer_id")
    k = k.filter(pl.col("report_date") < pl.col("period_start"))
    g = k.group_by("row_id").agg([(pl.col("line") == v).sum().alias(f"cust_n_{v}") for v in LINES])
    out = out.join(g, on="row_id", how="left").fill_null(0)
    out = out.join(rows.select("row_id", "pol_nclaims", "cust_nclaims", "pol_cost", "cust_cost"), on="row_id")
    out = out.with_columns(
        pol_freq=pl.col("pol_nclaims") / pl.col("hist_years"), cust_freq=pl.col("cust_nclaims") / pl.col("hist_years"),
        pol_costrate=pl.col("pol_cost") / pl.col("hist_years"), cust_costrate=pl.col("cust_cost") / pl.col("hist_years"),
        addr_freq=pl.col("addr_nclaims") / pl.col("hist_years"),
    ).drop("pol_nclaims", "cust_nclaims", "pol_cost", "cust_cost")
    out.write_parquet(f"work/feats_{line}.parquet")
    print(line, out.shape, out.select(pl.exclude("row_id").mean()).row(0, named=True), flush=True)


if __name__ == "__main__":
    claims, pmap = load_claims(), policy_map()
    for line in LINES:
        build(line, claims, pmap)
