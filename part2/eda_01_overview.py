"""Part 2 EDA 1: size, years, new business, claims and valuation of the emerging market against the developed one."""
import polars as pl
pl.Config.set_tbl_cols(30); pl.Config.set_tbl_width_chars(220)
D = "data/part2"
for mk in ("developed", "emerging"):
    print("=====", mk)
    for line in ("motor", "buildings", "contents"):
        p = pl.read_parquet(f"{D}/{mk}/policies_{line}.parquet"); t = pl.read_parquet(f"{D}/{mk}/test_{line}.parquet")
        p = p.with_columns(year=pl.col("period_start").dt.year()); t = t.with_columns(year=pl.col("period_start").dt.year())
        print(line, "train rows", len(p), "test rows", len(t), "policies", p["policy_id"].n_unique(), "test policies", t["policy_id"].n_unique(),
              "test policies seen in train", t["policy_id"].is_in(p["policy_id"]).mean().__round__(3))
        print(p.group_by("year").agg(rows=pl.len(), exposure=pl.col("exposure").sum().round(0), new=pl.col("new_business").mean().round(3),
                                     prem=pl.col("written_premium").sum().round(0)).sort("year"))
        print("test", t.group_by("year").agg(rows=pl.len(), exposure=pl.col("exposure").sum().round(0), new=pl.col("new_business").mean().round(3),
                                             prem=pl.col("written_premium").sum().round(0)))
    c = pl.read_parquet(f"{D}/{mk}/claims.parquet").with_columns(year=pl.col("loss_date").dt.year(), rep_lag=(pl.col("report_date") - pl.col("loss_date")).dt.total_days())
    print(c.group_by("line", "year").agg(n=pl.len(), repud=(pl.col("status") == "repudiated").mean().round(3), open=(pl.col("status") == "open").mean().round(3),
                                        inc=pl.col("incurred_to_date").mean().round(0), lag=pl.col("rep_lag").median()).sort("line", "year"))
