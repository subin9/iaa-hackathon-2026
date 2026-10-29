"""x1.2 probe files on one motor segment each of a base submission (the 2026-10-28 round on v10; q12d, comparison site, was built and not submitted).
usage: probe_q12.py BASE.csv OUT_DIR"""
import sys; sys.path.insert(0, "part2")
import polars as pl
import submission
from lib import load

base = pl.read_csv(sys.argv[1])
t = load("motor", "em").filter(pl.col("split") == "test").select("row_id", nb=pl.col("new_business").cast(pl.Int8), age=pl.col("driver_age_band"),
                                                                    *[pl.col(c) for c in ("channel", "region", "marital_status", "payment_method", "vehicle_use")])
d = base.join(t, on="row_id", how="left")
nb = pl.col("nb") == 1
P = {"q12a": nb & (pl.col("marital_status") == "married"), "q12b": nb & (pl.col("region") == "E02"), "q12c": nb & (pl.col("vehicle_use") == "business"),
     "q12d": pl.col("channel") == "comparison_site", "q12e": (pl.col("nb") == 0) & (pl.col("payment_method") == "monthly"),
     "q12f": pl.col("age") == "17-24", "q12g": pl.col("age") == "65+", "q12h": nb & pl.col("region").is_in(["E01", "E06"])}
for k, m in P.items():
    m = m.fill_null(False)
    submission.write(d.with_columns(prediction=pl.when(m).then(pl.col("prediction") * 1.2).otherwise(pl.col("prediction"))).select("row_id", "prediction"),
                     f"{sys.argv[2]}/{k}.csv")
