"""x1.2 probe files on one segment each of a base submission (the 2026-10-30 round on v13_cells). Segments are new-business rows picked from the
out-of-fold residual scan of the training new business; quintile cuts are those of the training new business (ncb_years 1 and 11, mean temperature 14.1).
usage: probe_q14.py BASE.csv OUT_DIR"""
import sys; sys.path.insert(0, "part2")
import polars as pl
import submission

base = pl.read_csv(sys.argv[1])
cols = {"motor": ["voluntary_excess", "prior_claims_5y", "ncb_years", "n_lines"], "contents": ["mean_temperature_c"]}
t = pl.concat([pl.read_parquet(f"work/clean/work/p2/{l}.parquet").filter(pl.col("split") == "test").select("row_id", "new_business", *c).with_columns(line=pl.lit(l))
               for l, c in cols.items()], how="diagonal_relaxed")
d = base.join(t, on="row_id", how="left")
mnb = (pl.col("line") == "motor") & pl.col("new_business")
P = {"q14a": mnb & (pl.col("voluntary_excess") == 0), "q14b": mnb & (pl.col("voluntary_excess") == 500), "q14c": mnb & (pl.col("prior_claims_5y") == 1),
     "q14d": mnb & (pl.col("ncb_years") >= 11), "q14e": mnb & (pl.col("ncb_years") < 1), "q14f": mnb & (pl.col("n_lines") == 2),
     "q14g": (pl.col("line") == "contents") & pl.col("new_business") & (pl.col("mean_temperature_c") < 14.1)}
for k, m in P.items():
    m = m.fill_null(False); print(k, "rows", d.filter(m).height)
    submission.write(d.with_columns(prediction=pl.when(m).then(pl.col("prediction") * 1.2).otherwise(pl.col("prediction"))).select("row_id", "prediction"),
                     f"{sys.argv[2]}/{k}.csv")
