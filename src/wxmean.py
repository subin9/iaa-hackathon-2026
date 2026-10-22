"""Weather split into the address's five-year mean and the current year's deviation from it.

The 2025 weather is shifted (mean wind index 4.87 against 4.34 to 4.60 in 2021 to 2024), so a model
that reads raw current-year values may treat a calendar shift as risk. Writes work/wxm_{line}.parquet.
"""
import polars as pl
from common import LINES

w = pl.read_parquet("data/public/weather.parquet")
V = [c for c in w.columns if c not in ("address_id", "year")]
m = w.group_by("address_id").agg([pl.col(c).mean().alias(c + "_m") for c in V])
for line in LINES:
    d = pl.read_parquet(f"work/{line}.parquet").select("row_id", "address_id", *V).join(m, on="address_id", how="left")
    d.select("row_id", *[pl.col(c + "_m") for c in V], *[(pl.col(c) - pl.col(c + "_m")).alias(c + "_d") for c in V]).write_parquet(f"work/wxm_{line}.parquet")
    print(line, d.shape)
