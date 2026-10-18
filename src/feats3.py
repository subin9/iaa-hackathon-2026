"""Period-shape features, written to work/feats3_{line}.parquet keyed by row_id.

Policy terms are cut at the calendar year end, so many rows are part-terms
that start on 1 January or end on 31 December. Claim frequency per unit of
exposure differs for those rows, and the season the row covers matters.
"""
import numpy as np, polars as pl
from prep import LINES

WINTER = {12, 1, 2}


def season_share(start, end):
    """Share of the row's days in Dec-Feb, by expanding each row's dates month by month."""
    out = np.zeros(len(start))
    for i, (s, e) in enumerate(zip(start, end)):
        d = np.arange(s, e + np.timedelta64(1, "D"), dtype="datetime64[D]")
        m = d.astype("datetime64[M]").astype(int) % 12 + 1
        out[i] = np.isin(m, list(WINTER)).mean()
    return out


def build(line):
    df = pl.read_parquet(f"work/{line}.parquet", columns=["row_id", "period_start", "period_end", "exposure"])
    df = df.with_columns(
        days=(pl.col("period_end") - pl.col("period_start")).dt.total_days() + 1,
        start_doy=pl.col("period_start").dt.ordinal_day(),
        end_doy=pl.col("period_end").dt.ordinal_day(),
        cut_start=(pl.col("period_start").dt.strftime("%m-%d") == "01-01") & (pl.col("exposure") < 0.985),
        cut_end=pl.col("period_end").dt.strftime("%m-%d").is_in(["12-30", "12-31"]) & (pl.col("exposure") < 0.985),
    )
    # month-level winter share is enough; compute on unique (start, end) pairs
    u = df.select("period_start", "period_end").unique()
    u = u.with_columns(winter_share=pl.Series(season_share(u["period_start"].to_numpy().astype("datetime64[D]"),
                                                            u["period_end"].to_numpy().astype("datetime64[D]"))))
    df = df.join(u, on=["period_start", "period_end"], how="left")
    out = df.select("row_id", "days", "start_doy", "end_doy", pl.col("cut_start").cast(pl.Int8), pl.col("cut_end").cast(pl.Int8), "winter_share")
    out.write_parquet(f"work/feats3_{line}.parquet")
    print(line, out.shape, out.select(pl.exclude("row_id").mean()).row(0, named=True), flush=True)


if __name__ == "__main__":
    for line in LINES:
        build(line)
