"""E24 scoring: the joint priors of e24_joint_prior.py through the final pipeline, each fold with the prior trained without that fold's emerging rows.
Compared with the developed-only power 1.6 prior alone (`_tm_p16`) and with v10's three-prior average, same folds, paired bootstrap by customer.
usage: e24_joint_cv.py TAG ...   (a tag "_jA+_tm_po+_tm_ex" puts the fold-specific joint prior in the average)"""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2
from e22_cleaned_round2 import dev, C, BASE


def prior(tag, line, k):
    ds = [pl.read_parquet(f"{C}/devperil{t}_k{k}_{line}.parquet" if t.startswith("_j") else f"{C}/devperil{t}_{line}.parquet") for t in tag.split("+")]
    return ds[0].select("row_id").with_columns(**{c: pl.Series(np.mean([d[c].to_numpy() for d in ds], 0)) for c in ds[0].columns if c != "row_id"})


def oof(tag):
    ys, out, cs = [], [], []
    for line in LINES:
        em = pl.read_parquet(f"{C}/{line}.parquet").filter(pl.col("split") == "train").sort("row_id")
        y = em["y"].to_numpy(); o = np.zeros(len(y))
        for k, (tri, vai) in enumerate(GroupKFold(5).split(em, y, em["customer_id"].to_numpy())):
            e = em.join(prior(tag, line, k), on="row_id").sort("row_id")
            o[vai] = model2.pipeline(e[tri], e[vai], short=model2.SHORT[line], score_is_train=True)
        ys.append(y); out.append(o); cs.append(em["customer_id"].to_numpy())
    return np.concatenate(ys), np.concatenate(out), np.concatenate(cs)


Y, G = None, None
refs = {}
for ref in ("_tm_p16", BASE):
    Y, refs[ref], G = oof(ref)
u, g = np.unique(G, return_inverse=True); d0 = np.bincount(g, dev(Y, np.full(len(Y), Y.mean())))
for ref, A in refs.items(): print(f"{ref:28s} D2 {1 - np.bincount(g, dev(Y, A)).sum() / d0.sum():.5f}", flush=True)
for tag in sys.argv[1:]:
    _, B, _ = oof(tag); dB = np.bincount(g, dev(Y, B)); line = f"{tag:28s} D2 {1 - dB.sum() / d0.sum():.5f}"
    for ref, A in refs.items():
        dA = np.bincount(g, dev(Y, A)); rng = np.random.default_rng(0)
        diff = np.array([(dA[i].sum() - dB[i].sum()) / d0[i].sum() for i in (rng.integers(0, len(u), len(u)) for _ in range(2000))])
        line += f" | vs {ref} {(dA.sum() - dB.sum()) / d0.sum():+.5f} sd {diff.std():.5f} P {(diff > 0).mean():.3f}"
    print(line, flush=True)
