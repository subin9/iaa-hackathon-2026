"""E21: the teammate's cleaned emerging files (data/part2_cleaned, built into work/clean by the same prep_emerging.py and harmonize.py) through the final pipeline.
The cleaning fills missing vehicle_age, engine_size_cc, overnight_parking, smoke_alarms, security_level and high_value_items from the same policy's other rows,
fixes units (already fixed in prep) and drops 36 claims reported more than a year late (none falls inside a training period, so y is unchanged).
Also the teammate's feature list: renewal_count kept, compulsory_excess dropped, vehicle details kept, gender not used.
Same 5 folds grouped by customer on both data sets (rows sorted by row_id), paired bootstrap by customer against the v9 recipe on the original data."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2


def prior(root, tag, line):
    ds = [pl.read_parquet(f"{root}/devperil{t}_{line}.parquet") for t in tag.split("+")]
    return ds[0].select("row_id").with_columns(**{c: pl.Series(np.mean([d[c].to_numpy() for d in ds], 0)) for c in ds[0].columns if c != "row_id"})


def oof(root, tag, gender=True):
    ys, out, cs = [], [], []
    for line in LINES:
        em = pl.read_parquet(f"{root}/{line}.parquet").filter(pl.col("split") == "train").join(prior(root, tag, line), on="row_id").sort("row_id")
        short = model2.SHORT[line] if gender or line != "motor" else []
        y = em["y"].to_numpy(); o = np.zeros(len(y))
        for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
            o[vai] = model2.pipeline(em[tri], em[vai], short=short, score_is_train=True)
        ys.append(y); out.append(o); cs.append(em["customer_id"].to_numpy())
    return np.concatenate(ys), np.concatenate(out), np.concatenate(cs)


def dev(y, m): return 4 * (y * m ** -0.5 + m ** 0.5 - 2 * np.sqrt(y))   # unit Tweedie 1.5 deviance per row


O, C = "work/p2", "work/clean/work/p2"
V9 = "_x_p16+_v_po+_v_ex"
Y, A, G = oof(O, V9)
u, g = np.unique(G, return_inverse=True); dA = np.bincount(g, dev(Y, A)); d0 = np.bincount(g, dev(Y, np.full(len(Y), Y.mean())))
print(f"{'original, v9 recipe':44s} D2 {1 - dA.sum() / d0.sum():.5f}", flush=True)
RUNS = [("cleaned, v9 recipe", C, V9, True), ("cleaned, v7 recipe", C, "_v_tw+_v_po+_v_ex", True),
        ("cleaned, v9 recipe, no gender", C, V9, False), ("original, v9 recipe, no gender", O, V9, False),
        ("cleaned, teammate features (p16 part)", C, "_tm_p16+_v_po+_v_ex", True), ("cleaned, teammate features, no gender", C, "_tm_p16+_v_po+_v_ex", False),
        ("cleaned, renewal_count kept (p16 part)", C, "_rc_p16+_v_po+_v_ex", True), ("cleaned, compulsory_excess dropped (p16 part)", C, "_xs_p16+_v_po+_v_ex", True),
        ("cleaned, p16 alone", C, "_x_p16", True), ("cleaned, teammate features p16 alone", C, "_tm_p16", True),
        ("cleaned, teammate features in all three priors", C, "_tm_p16+_tm_po+_tm_ex", True)]
RUNS = [r for r in RUNS if not sys.argv[1:] or r[0] in sys.argv[1:]]   # optional: run only the named rows
for name, root, tag, gender in RUNS:
    Yb, B, _ = oof(root, tag, gender); assert np.allclose(Yb, Y)
    dB = np.bincount(g, dev(Y, B)); rng = np.random.default_rng(0)
    diff = np.array([(dA[i].sum() - dB[i].sum()) / d0[i].sum() for i in (rng.integers(0, len(u), len(u)) for _ in range(2000))])
    print(f"{name:44s} D2 {1 - dB.sum() / d0.sum():.5f}  gain over original v9 {(dA.sum() - dB.sum()) / d0.sum():+.5f}  sd {diff.std():.5f}  P(gain>0) {(diff > 0).mean():.3f}", flush=True)
