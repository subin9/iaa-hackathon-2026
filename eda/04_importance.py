import sys; sys.path.insert(0, "src")
import numpy as np, polars as pl
from common import load
from gbm import fit
df = load("contents").filter(pl.col("split")=="train")
f = fit(df.filter(pl.col("year")<=2023), 300)
imp = f["model"].feature_importance("gain"); names = f["model"].feature_name()
for i in np.argsort(-imp)[:15]: print(f"{names[i]:30s} {imp[i]/imp.sum():.3f}")
print(df.group_by("customer_service_contacts").agg(pl.len(), freq=(pl.col("n")>0).mean()).sort("customer_service_contacts"))
