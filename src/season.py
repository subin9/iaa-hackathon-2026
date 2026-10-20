"""Seasonal exposure features: the mean monthly claim index over each row's covered days.

The monthly cost and frequency indices per line come from 2021-2022 claims over
policy-days, which both validation folds train on. A row covering only winter
months gets a higher index than a full-year row with the same exposure.
Writes work/season_{line}.parquet with season_cost, season_freq and winter_share.
"""
import numpy as np, polars as pl
from common import LINES

claims = pl.read_parquet("data/public/claims.parquet").with_columns(
    cost=pl.col("incurred_to_date") - pl.col("recoveries"), m=pl.col("loss_date").cast(pl.Date).dt.month(), yr=pl.col("loss_date").cast(pl.Date).dt.year())


def month_days(rows):
    """Covered days per calendar (year, month) bucket, without expanding rows to days."""
    rows = rows.with_columns(pl.col("period_start").cast(pl.Date), pl.col("period_end").cast(pl.Date))
    out = []
    for y in range(2020, 2027):
        for m in range(1, 13):
            a, b = pl.date(y, m, 1), pl.date(y + (m == 12), m % 12 + 1, 1)
            ov = (pl.min_horizontal(pl.col("period_end"), b) - pl.max_horizontal(pl.col("period_start"), a)).dt.total_days().clip(0)
            out.append(rows.select("row_id", n=ov, y=pl.lit(y), m=pl.lit(m)).filter(pl.col("n") > 0))
    return pl.concat(out)


for line in LINES:
    cols = ["row_id", "period_start", "period_end"]
    rows = pl.concat([pl.read_parquet(f"data/public/policies_{line}.parquet").select(cols), pl.read_parquet(f"data/public/test_{line}.parquet").select(cols)])
    d = month_days(rows)
    mature = d.filter(pl.col("y").is_between(2021, 2022)).group_by("m").agg(len=pl.col("n").sum())
    c = claims.filter((pl.col("line") == line) & pl.col("yr").is_between(2021, 2022)).group_by("m").agg(pl.col("cost").sum(), n=pl.len())
    s = mature.join(c, on="m").with_columns(sc=pl.col("cost") / pl.col("len"), sn=pl.col("n") / pl.col("len"))
    s = s.with_columns(sc=pl.col("sc") / pl.col("sc").mean(), sn=pl.col("sn") / pl.col("sn").mean()).select("m", "sc", "sn")
    out = d.join(s, on="m").group_by("row_id").agg(
        season_cost=(pl.col("sc") * pl.col("n")).sum() / pl.col("n").sum(), season_freq=(pl.col("sn") * pl.col("n")).sum() / pl.col("n").sum(),
        winter_share=(pl.col("m").is_in([12, 1, 2]) * pl.col("n")).sum() / pl.col("n").sum())
    out.write_parquet(f"work/season_{line}.parquet")
    print(line, out.height, "rows of", rows.height)
