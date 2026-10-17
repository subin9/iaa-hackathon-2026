import polars as pl
D = "data/public/"
c = pl.read_parquet(D+"claims.parquet").with_columns(
    ay=pl.col("loss_date").dt.year(),
    lag=(pl.col("report_date")-pl.col("loss_date")).dt.total_days(),
    net=pl.col("incurred_to_date")-pl.col("recoveries"))
print(c.describe())
print(c.group_by("status").agg(pl.len(), pl.col("incurred_to_date").sum(), pl.col("paid_to_date").sum()))
print("loss_date range", c["loss_date"].min(), c["loss_date"].max(), "report max", c["report_date"].max())
print(c.filter(pl.col("status")=="repudiated").select(pl.col("incurred_to_date","paid_to_date","recoveries").sum()))
print(c.group_by("line","ay").agg(n=pl.len(), open=(pl.col("status")=="open").mean(), net=pl.col("net").filter(pl.col("status")!="repudiated").sum(), lag_med=pl.col("lag").median(), lag_p95=pl.col("lag").quantile(.95)).sort("line","ay"))
# report lag distribution by line (claims from 2021-2022 have full reporting)
print(c.filter(pl.col("ay")<=2022).group_by("line").agg([ (pl.col("lag")<=d).mean().alias(f"<= {d}d") for d in (30,90,180,365,730)]))
# match claims to policy rows
w = pl.read_parquet(D+"weather.parquet"); print("weather years", sorted(w["year"].unique().to_list()))
for line, f in [("motor","policies_motor"),("buildings","policies_buildings"),("contents","policies_contents")]:
    p = pl.read_parquet(D+f+".parquet", columns=["row_id","policy_id","period_start","period_end","exposure","written_premium"])
    m = c.filter(pl.col("line")==line).join(p, on="policy_id", how="left").filter(pl.col("loss_date").is_between(pl.col("period_start"),pl.col("period_end")))
    print(line, "claims", c.filter(pl.col("line")==line).height, "matched rows", m.height, "unique claims matched", m["claim_id"].n_unique())
    t = m.filter(pl.col("status")!="repudiated").group_by("row_id").agg(y=pl.col("net").sum())
    p = p.join(t, on="row_id", how="left").with_columns(pl.col("y").fill_null(0), yr=pl.col("period_start").dt.year())
    print(p.group_by("yr").agg(expo=pl.col("exposure").sum(), cost_per_expo=pl.col("y").sum()/pl.col("exposure").sum(), lr=pl.col("y").sum()/pl.col("written_premium").sum(), freq=(pl.col("y")>0).sum()/pl.col("exposure").sum(), prem_per_expo=pl.col("written_premium").sum()/pl.col("exposure").sum()).sort("yr"))
