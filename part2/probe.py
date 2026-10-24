"""LB probe builder: multiply segments of a submission by factors.
usage: probe.py IN.csv OUT.csv "line=motor,nb=1:1.10" ["channel=direct,line=motor,nb=1:1.2" ...]   (segment spec, a colon, the factor)"""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
import submission, segments
sub = pl.read_csv(sys.argv[1]); d = segments.test_frame(sub); f = np.ones(len(d))
for item in sys.argv[3:]:
    spec, fac = item.rsplit(":", 1); f = np.where(segments.mask(d, spec), f * float(fac), f)
out = d.with_columns(prediction=pl.Series(d["prediction"].to_numpy() * f)).select("row_id", "prediction")
print("total before", round(float(sub["prediction"].sum())), "after", round(float(out["prediction"].sum())))
submission.write(out, sys.argv[2])
