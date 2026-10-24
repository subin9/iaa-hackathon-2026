"""Submission v0: developed prior x one level factor per line (fitted on emerging 2023-24, completion-adjusted), no corrections, no trend."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import *
import submission
parts = []
for line in LINES:
    em = load(line, "em").join(pl.read_parquet(f"work/p2/devprior_{line}.parquet"), on="row_id")
    tr = em.filter(pl.col("split") == "train"); te = em.filter(pl.col("split") == "test")
    k = tr["y"].sum() / (np.exp(tr["lr_dev"].to_numpy()) * offset(tr)).sum()
    p = k * np.exp(te["lr_dev"].to_numpy()) * te["exposure"].to_numpy()
    print(line, "k", round(float(k), 3), "mean predicted rate per exposure year", round(float(p.sum() / te["exposure"].sum()), 1))
    parts.append(pl.DataFrame({"row_id": te["row_id"], "prediction": p}))
submission.write(pl.concat(parts), "work/p2/sub_v0.csv")
