"""Claim history as the data cutoff would show it, for every row.

The claims file ends on 2024-12-30, so a 2025 test row that starts in June sees no claims
reported between January and June, and one that starts in December sees almost none of
the year before it. prep.history counts everything reported before period_start, so
training rows see more history than test rows. Here every row counts only claims
reported before the end of the previous calendar year (and before period_start), which
is what a 2025 row sees. Writes work/hasof_{line}.parquet with the prep.history columns.
"""
import polars as pl
from prep import D, LINES, load_claims


def history(claims, rows):
    pol = claims.select("policy_id", "line", "report_date", "net")
    cust_map = pl.concat([pl.read_parquet(D + f"{f}_{l}.parquet", columns=["policy_id", "customer_id"])
                          for f in ("policies", "test") for l in LINES]).unique("policy_id")
    cust = pol.join(cust_map, on="policy_id")
    out = rows.select("row_id", "policy_id", "customer_id", "period_start",
                      cut=pl.min_horizontal(pl.col("period_start"), pl.date(pl.col("period_start").dt.year() - 1, 12, 31)))
    for key, src, name in [("policy_id", pol, "pol"), ("customer_id", cust, "cust")]:
        j = out.select("row_id", key, "period_start", "cut").join(src.select(key, "report_date", "net"), on=key)
        j = j.filter(pl.col("report_date") < pl.col("cut"))
        g = j.group_by("row_id").agg(
            pl.len().alias(f"{name}_nclaims"),
            pl.col("net").sum().alias(f"{name}_cost"),
            (pl.col("report_date") >= pl.col("period_start").dt.offset_by("-1y")).sum().alias(f"{name}_nclaims_1y"),
        )
        out = out.join(g, on="row_id", how="left")
    return out.drop("policy_id", "customer_id", "period_start", "cut").fill_null(0)


if __name__ == "__main__":
    claims = load_claims()
    for line in LINES:
        rows = pl.read_parquet(f"work/{line}.parquet", columns=["row_id", "policy_id", "customer_id", "period_start", "year"])
        h = history(claims, rows)
        h.write_parquet(f"work/hasof_{line}.parquet")
        print(line, h.join(rows.select("row_id", "year"), on="row_id").group_by("year").agg(pl.col("pol_nclaims_1y").mean().round(4)).sort("year").rows(), flush=True)
