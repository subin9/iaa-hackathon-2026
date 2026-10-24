"""Submission v1: new-business-aware developed prior x one level per line (emerging 2023-24, completion-adjusted)."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import *
import submission
TAG_ = sys.argv[1] if len(sys.argv) > 1 else "_nb"; OUT = sys.argv[2] if len(sys.argv) > 2 else "work/p2/sub_v1.csv"
parts = []
for line in LINES:
    em = load(line, "em").join(pl.read_parquet(f"work/p2/devprior{TAG_}_{line}.parquet"), on="row_id")
    tr = em.filter(pl.col("split") == "train"); te = em.filter(pl.col("split") == "test")
    k = tr["y"].sum() / (np.exp(tr["lr_dev"].to_numpy()) * offset(tr)).sum()
    p = k * np.exp(te["lr_dev"].to_numpy()) * te["exposure"].to_numpy()
    print(line, "k", round(float(k), 3), "mean predicted rate per exposure year", round(float(p.sum() / te["exposure"].sum()), 1))
    parts.append(pl.DataFrame({"row_id": te["row_id"], "prediction": p}))
submission.write(pl.concat(parts), OUT)
