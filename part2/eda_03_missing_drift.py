"""Part 2 EDA 3: where the ~12% missing values sit, and how test rows differ from training rows in the emerging market."""
import polars as pl
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_width_chars(200)
D = "data/part2/emerging/"
cust = pl.read_parquet(D + "customers.parquet"); addr = pl.read_parquet(D + "addresses.parquet")
for line in ("motor", "buildings", "contents"):
    tr = pl.read_parquet(D + f"policies_{line}.parquet").with_columns(split=pl.lit("train")); te = pl.read_parquet(D + f"test_{line}.parquet").with_columns(split=pl.lit("test"))
    df = pl.concat([tr.drop("renewal_decision"), te], how="diagonal_relaxed").join(cust, on="customer_id", how="left").join(addr, on="address_id", how="left")
    df = df.with_columns(year=pl.col("period_start").dt.year())
    miss = [c for c in df.columns if 0.05 < df[c].null_count() / len(df) < 0.3]
    print("\n=====", line, "columns with 5-30% missing:", miss)
    # missing share by split/year/channel/new business
    for key in ("year", "channel", "new_business", "region"):
        print(df.group_by(key).agg(n=pl.len(), **{c[:10]: pl.col(c).is_null().mean().round(3) for c in miss[:6]}).sort(key))
    # is missingness joint? share of rows with 0, 1..k missing among those columns
    k = df.select(pl.sum_horizontal([pl.col(c).is_null().cast(pl.Int32) for c in miss]).alias("k"))["k"]
    print("number of missing among the columns:", k.value_counts().sort("k").rows())
