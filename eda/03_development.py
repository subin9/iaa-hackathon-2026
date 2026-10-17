import polars as pl
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_cols(20); pl.Config.set_tbl_width_chars(200)
c = pl.read_parquet("data/public/claims.parquet").filter(pl.col("status")!="repudiated").with_columns(
    ay=pl.col("loss_date").dt.year(), net=pl.col("incurred_to_date")-pl.col("recoveries"),
    age_m=((pl.date(2024,12,31)-pl.col("loss_date")).dt.total_days()/30.4).floor())
c = c.filter(pl.col("ay")>=2021)
print(c.group_by("line","peril","ay").agg(n=pl.len(), open=(pl.col("status")=="open").mean(), sev=pl.col("net").mean(), sev_closed=pl.col("net").filter(pl.col("status")=="closed").mean(), sev_open=pl.col("net").filter(pl.col("status")=="open").mean(), paid_over_inc_open=(pl.col("paid_to_date").filter(pl.col("status")=="open").sum()/pl.col("incurred_to_date").filter(pl.col("status")=="open").sum()), rec=pl.col("recoveries").sum()/pl.col("incurred_to_date").sum()).sort("line","peril","ay"))
# 2024 monthly counts vs 2023 same month (IBNR in counts)
m = c.with_columns(mo=pl.col("loss_date").dt.month()).group_by("line","ay","mo").agg(pl.len()).pivot(on="ay", index=["line","mo"], values="len").sort("line","mo")
print(m)
print(c.sort("net", descending=True).head(15).select("line","peril","ay","status","net","incurred_to_date","paid_to_date"))
