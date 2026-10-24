"""Average per-peril prior variants in log space. usage: average_priors.py TAG1 TAG2 ... OUT_TAG"""
import sys
import numpy as np, polars as pl
*tags, out = sys.argv[1:]
for line in ("motor", "buildings", "contents"):
    ds = [pl.read_parquet(f"work/p2/devperil{t}_{line}.parquet") for t in tags]
    assert all(d["row_id"].to_list() == ds[0]["row_id"].to_list() for d in ds)
    cols = [c for c in ds[0].columns if c != "row_id"]
    ds[0].select("row_id").with_columns(**{c: pl.Series(np.mean([d[c].to_numpy() for d in ds], 0)) for c in cols}).write_parquet(f"work/p2/devperil{out}_{line}.parquet")
    print(line, "averaged", tags, "->", out)
