"""Money features relative to their calendar-year median, so 2025 rate increases do not read as risk.

Premium rate rises 23 to 39 percent from 2021 to 2025 and sum insured 8 to 13 percent, so the
2025 rows sit at the edge of the training range on raw values. Writes work/defl_{line}.parquet.
"""
import polars as pl
from common import LINES

for line in LINES:
    d = pl.read_parquet(f"work/{line}.parquet")
    cols = [c for c in ("premium_rate", "written_premium", "sum_insured") if c in d.columns]
    d.select("row_id", *[(pl.col(c) / pl.col(c).median().over("year")).alias(c + "_rel") for c in cols]).write_parquet(f"work/defl_{line}.parquet")
    print(line, cols)
