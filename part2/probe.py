"""LB probe builder: take a submission csv, multiply predictions of a segment by a factor.
usage: probe.py IN.csv OUT.csv "line=motor,nb=1:1.10" ["line=...:f" ...]   (segments: line=, nb=0|1, joined by comma; the factor follows the colon)"""
import sys; sys.path.insert(0, "part2")
import polars as pl
from lib import *
import submission
sub = pl.read_csv(sys.argv[1]); seg = pl.concat([load(l, "em").filter(pl.col("split") == "test").select("row_id", "new_business", line=pl.lit(l)) for l in LINES])
d = sub.join(seg, on="row_id"); f = pl.lit(1.0)
for spec in sys.argv[3:]:
    cond, fac = spec.split(":"); m = pl.lit(True)
    for kv in cond.split(","):
        k, v = kv.split("="); m = m & ((pl.col("line") == v) if k == "line" else (pl.col("new_business") == (v == "1")))
    f = f * pl.when(m).then(float(fac)).otherwise(1.0)
out = d.with_columns(prediction=pl.col("prediction") * f).select("row_id", "prediction")
print("total before", round(float(sub["prediction"].sum())), "after", round(float(out["prediction"].sum())))
submission.write(out, sys.argv[2])
