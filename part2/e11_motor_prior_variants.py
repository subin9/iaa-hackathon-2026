"""E11: motor only, pipeline CV (levels + gender) for prior variants given as tags."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2
for tag in sys.argv[1:]:
    em = load("motor", "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil{tag}_motor.parquet"), on="row_id")
    ye = em["y"].to_numpy(); o = np.zeros(len(ye)); o2 = np.zeros(len(ye))
    for tri, vai in GroupKFold(5).split(em, ye, em["customer_id"].to_numpy()):
        o[vai] = model2.pipeline(em[tri], em[vai], short=[], score_is_train=True); o2[vai] = model2.pipeline(em[tri], em[vai], short=["gender"], score_is_train=True)
    print(f"{tag:10s} motor D2 levels {d2(ye, o):.4f}  +gender {d2(ye, o2):.4f}")
