"""E17: new prior variants through the final pipeline, same 5 folds grouped by customer as e10. Variants (devprior_peril.py knobs): covariate-shift weights
(P2_CSW=1, developed rows weighted to look like the emerging rows), deeper trees (P2_LEAVES=7), Tweedie power 1.6 (P2_POWER). Compare each with _v_tw, the same
Tweedie 1.4 prior without the knob, and inside the three-way average in place of _v_tw.
usage: e17_prior_cv.py TAG ...   (a tag "a+b+c" averages those priors in log space)"""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2


def prior(tag, line):
    ds = [pl.read_parquet(f"work/p2/devperil{t}_{line}.parquet") for t in tag.split("+")]
    return ds[0].select("row_id").with_columns(**{c: pl.Series(np.mean([d[c].to_numpy() for d in ds], 0)) for c in ds[0].columns if c != "row_id"})


for tag in sys.argv[1:]:
    ys, out, per = [], [], {}
    for line in LINES:
        em = load(line, "em").filter(pl.col("split") == "train").join(prior(tag, line), on="row_id")
        y = em["y"].to_numpy(); o = np.zeros(len(y))
        for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
            o[vai] = model2.pipeline(em[tri], em[vai], short=model2.SHORT[line], score_is_train=True)
        ys.append(y); out.append(o); per[line] = round(d2(y, o), 4)
    print(f"{tag:28s}", per, "pooled", round(d2(np.concatenate(ys), np.concatenate(out)), 4), flush=True)
