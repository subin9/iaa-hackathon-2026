"""Geometric mean of two submissions, optionally times the row ratio NUM / DEN of two more. v12c: v9 and v10, times the fire term as v12a / v10
(the result goes through transplant_cells.py, which removes any constant per cell).
usage: geo_mean.py A.csv B.csv OUT.csv [NUM.csv DEN.csv]"""
import sys
import polars as pl

a, b = (pl.read_csv(f) for f in sys.argv[1:3])
d = a.join(b, on="row_id", suffix="_b").select("row_id", prediction=(pl.col("prediction") * pl.col("prediction_b")).sqrt())
if len(sys.argv) > 5:
    n, m = (pl.read_csv(f) for f in sys.argv[4:6])
    f = n.join(m, on="row_id", suffix="_d").select("row_id", f=pl.col("prediction") / pl.col("prediction_d"))
    d = d.join(f, on="row_id").select("row_id", prediction=pl.col("prediction") * pl.col("f"))
d.write_csv(sys.argv[3]); print("wrote", sys.argv[3], len(d), "rows")
