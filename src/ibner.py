"""IBNER correction for open bodily injury claims of accident year 2024.

At the 31 Dec 2024 valuation, open 2024 bodily injury claims carry about the
same incurred as closed ones, while in earlier years open claims run well
above closed ones. The 2024 mean severity at report lags up to a year sits
about 30% under the log-linear trend of 2021-2023. Scaling the open 2024
claims by k brings the 2024 mean back on trend. Writes work/ibner_add.parquet
with the extra cost per row; common.load adds it to y when IBNER=1.
"""
import numpy as np, polars as pl
from prep import load_claims
from common import LINES

c = load_claims().filter(pl.col("status") != "repudiated").with_columns(ay=pl.col("loss_date").dt.year())
bi = c.filter((pl.col("peril") == "bodily_injury") & (pl.col("lag") <= 365))
s = bi.group_by("ay").agg(m=pl.col("net").mean(), n=pl.len(), open=(pl.col("status") == "open").mean(),
                          mo=pl.col("net").filter(pl.col("status") == "open").mean(),
                          mc=pl.col("net").filter(pl.col("status") == "closed").mean()).sort("ay")
ref = s.filter(pl.col("ay").is_between(2021, 2023))
g = np.polyfit(ref["ay"].to_numpy(), np.log(ref["m"].to_numpy()), 1)
r = s.filter(pl.col("ay") == 2024).row(0, named=True)
k = (np.exp(np.polyval(g, 2024)) - r["mc"] * (1 - r["open"])) / (r["mo"] * r["open"])
print("k", round(k, 3))
adj = c.filter((pl.col("peril") == "bodily_injury") & (pl.col("ay") == 2024) & (pl.col("status") == "open")).select(
    "policy_id", "loss_date", add=pl.col("net") * (k - 1))
rows = pl.concat([pl.read_parquet(f"work/{l}.parquet", columns=["row_id", "policy_id", "period_start", "period_end"]) for l in LINES])
m = adj.join(rows, on="policy_id").filter(pl.col("loss_date").is_between(pl.col("period_start"), pl.col("period_end")))
out = m.group_by("row_id").agg(pl.col("add").sum())
out.write_parquet("work/ibner_add.parquet")
print(out.height, "rows, added", round(out["add"].sum()))
