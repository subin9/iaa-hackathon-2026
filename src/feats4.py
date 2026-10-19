"""Row-sequence features from the policy's own row history.

post_mtc     the row continues a row of the same policy that ended the day before in the same year
pre_mtc      the row ends early and the policy has a later row in the same year
ends_early   the row ends before the year end with no later row that year (cancelled or lapsed)
prev_dec     the previous row of the policy carries renewal_decision declined_by_insurer
All of these are visible for 2025 test rows: period dates are given, and
decisions are known for every training row.
"""
import polars as pl
from common import LINES, load

D = "data/public/"


def main():
    rd = pl.concat([pl.read_parquet(D + f"policies_{l}.parquet", columns=["row_id", "renewal_decision"]) for l in LINES])
    for line in LINES:
        r = load(line).select("row_id", "policy_id", "period_start", "period_end", "year").join(rd, on="row_id", how="left")
        r = r.sort("policy_id", "period_start").with_columns(
            prv_end=pl.col("period_end").shift(1).over("policy_id"),
            nxt_start=pl.col("period_start").shift(-1).over("policy_id"),
            prv_dec=pl.col("renewal_decision").shift(1).over("policy_id"))
        full = pl.col("period_end").dt.strftime("%m-%d").is_in(["12-30", "12-31"])
        r = r.select("row_id",
                     post_mtc=((pl.col("period_start") - pl.col("prv_end")).dt.total_days() == 1) & (pl.col("prv_end").dt.year() == pl.col("year")) & (pl.col("period_start").dt.strftime("%m-%d") != "01-01"),
                     pre_mtc=~full & (pl.col("nxt_start").dt.year() == pl.col("year")),
                     ends_early=~full & ~(pl.col("nxt_start").dt.year() == pl.col("year")).fill_null(False),
                     prev_dec=pl.col("prv_dec") == "declined_by_insurer")
        r = r.with_columns(pl.all().exclude("row_id").fill_null(False).cast(pl.Int8))
        r.write_parquet(f"work/feats4_{line}.parquet")
        print(line, r.select(pl.all().exclude("row_id").mean()).rows())


if __name__ == "__main__":
    main()
