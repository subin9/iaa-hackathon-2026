"""E20: paired bootstrap (by customer) of the CV D2 difference between prior variants and the current average, same folds."""
import sys; sys.path.insert(0,"part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2
from e17_prior_cv import prior
def oof(tag):
    ys, out, cs = [], [], []
    for line in LINES:
        em = load(line,"em").filter(pl.col("split")=="train").join(prior(tag,line), on="row_id")
        y = em["y"].to_numpy(); o = np.zeros(len(y))
        for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
            o[vai] = model2.pipeline(em[tri], em[vai], short=model2.SHORT[line], score_is_train=True)
        ys.append(y); out.append(o); cs.append(em["customer_id"].to_numpy())
    return np.concatenate(ys), np.concatenate(out), np.concatenate(cs)
def dev(y, m): return 4*(y*m**-0.5 + m**0.5 - 2*np.sqrt(y))   # unit Tweedie 1.5 deviance per row
Y, A, C = oof("_v_tw+_v_po+_v_ex")
for tag in ("_x_p16+_v_po+_v_ex", "_x_l7+_v_po+_v_ex"):
    _, B, _ = oof(tag)
    u, g = np.unique(C, return_inverse=True); dA = np.bincount(g, dev(Y, A)); dB = np.bincount(g, dev(Y, B)); d0 = np.bincount(g, dev(Y, np.full(len(Y), Y.mean())))
    rng = np.random.default_rng(0); diff = []
    for _ in range(2000):
        i = rng.integers(0, len(u), len(u)); diff.append((dA[i].sum() - dB[i].sum()) / d0[i].sum())
    diff = np.array(diff); print(tag, "D2 gain over current", round((dA.sum()-dB.sum())/d0.sum(), 5), "bootstrap sd", round(diff.std(), 5), "P(gain>0)", round((diff > 0).mean(), 3))
