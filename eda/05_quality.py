import polars as pl
D = "data/public/"
c = pl.read_parquet(D+"claims.parquet")
print("dup claim_id", c.height - c["claim_id"].n_unique())
key = ["policy_id","peril","loss_date","incurred_to_date"]
print("dup claim content", c.height - c.unique(key).height)
print(c.filter(pl.struct(key).is_duplicated()).sort(key).head(6))
print("checks", c.select(neg_inc=(pl.col("incurred_to_date")<0).sum(), neg_rec=(pl.col("recoveries")<0).sum(), paid_gt_inc=(pl.col("paid_to_date")>pl.col("incurred_to_date")+0.01).sum(), rec_gt_inc=(pl.col("recoveries")>pl.col("incurred_to_date")).sum(), rep_before_loss=(pl.col("report_date")<pl.col("loss_date")).sum()))
print("dups by line", c.filter(pl.struct(key).is_duplicated()).group_by("line","status").agg(pl.len()))
print("closed paid!=incurred", c.filter(pl.col("status")=="closed").select(((pl.col("paid_to_date")-pl.col("incurred_to_date")).abs()>0.01).sum()))
for l in ["motor","buildings","contents"]:
    for f in ("policies","test"):
        p = pl.read_parquet(D+f"{f}_{l}.parquet")
        print(l, f, "dup row_id", p.height-p["row_id"].n_unique(), "dup content", p.height - p.drop("row_id").unique().height)
        num = [k for k,t in p.schema.items() if t.is_numeric()]
        print(p.select(num).describe().filter(pl.col("statistic").is_in(["min","max"])))
    # overlapping periods for same policy
    p = pl.read_parquet(D+f"policies_{l}.parquet").sort("policy_id","period_start")
    print("overlap", p.with_columns(prev_end=pl.col("period_end").shift().over("policy_id")).filter(pl.col("period_start")<=pl.col("prev_end")).height)
cu = pl.read_parquet(D+"customers.parquet"); print(cu.select(pl.col("date_of_birth").min(), pl.col("date_of_birth").max()), "dup cust", cu.height-cu["customer_id"].n_unique())
