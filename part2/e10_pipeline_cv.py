"""E10: the full Part 2 pipeline in a 5-fold CV grouped by customer, with variants of the correction stage."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2
TAGP = sys.argv[1] if len(sys.argv) > 1 else "_nb"
VARS = {"levels only": {l: [] for l in LINES},
        "gender(motor)": {"motor": ["gender"], "buildings": [], "contents": []},
        "gender+NB (motor)": {"motor": ["gender", "new_business"], "buildings": [], "contents": []},
        "gender+NB motor, age buildings": {"motor": ["gender", "new_business"], "buildings": ["policyholder_age_band"], "contents": []},
        "above + NB everywhere": {"motor": ["gender", "new_business"], "buildings": ["policyholder_age_band", "new_business"], "contents": ["new_business"]},
        "gender all + age all + NB all": {l: ["gender", "new_business", "driver_age_band" if l == "motor" else "policyholder_age_band"] for l in LINES}}
out = {v: [] for v in VARS}; ys = []; per = {v: {} for v in VARS}
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil{TAGP}_{line}.parquet"), on="row_id")
    ye = em["y"].to_numpy(); ys.append(ye); folds = list(GroupKFold(5).split(em, ye, em["customer_id"].to_numpy()))
    for v, sh in VARS.items():
        o = np.zeros(len(ye))
        for tri, vai in folds:
            o[vai] = model2.pipeline(em[tri], em[vai], short=sh[line], score_is_train=True)
        out[v].append(o); per[v][line] = round(d2(ye, o), 4)
Y = np.concatenate(ys)
for v in VARS: print(f"{v:34s}", per[v], "pooled", round(d2(Y, np.concatenate(out[v])), 4))
