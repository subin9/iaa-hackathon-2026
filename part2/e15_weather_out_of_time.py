"""E15: does the weather of the row's own year help out of time? The 2025 weather is in the data (weather.parquet has 2025 rows in both markets), so a weather prior
would use the realised 2025 weather. Test: fit the pipeline on the 2023 rows, score the 2024 rows, priors without weather (_nb), with weather on glass_hail, storm and
subsidence (_nbwx2) and on every weather peril (_nbwx). D2 raw / with the total re-matched, and the 2024 A/E."""
import sys; sys.path.insert(0,"part2")
import numpy as np, polars as pl
from lib import *
import model2
for tag in ("_nb","_nbwx2","_nbwx"):
    parts=[]; out=[]
    for line in LINES:
        em = load(line,"em").filter(pl.col("split")=="train").join(pl.read_parquet(f"work/p2/devperil{tag}_{line}.parquet"), on="row_id")
        tr, va = em.filter(pl.col("year")==2023), em.filter(pl.col("year")==2024)
        p = model2.pipeline(tr, va, short=model2.SHORT[line], score_is_train=True); y = va["y"].to_numpy()
        parts.append((y,p)); out.append(f"{line} {d2(y,p):.4f}/{d2(y,p*y.sum()/p.sum()):.4f} A/E {y.sum()/p.sum():.3f}")
    print(tag, " | ".join(out), "| pooled raw/rematched", [round(v,4) for v in pooled_d2(parts)])
