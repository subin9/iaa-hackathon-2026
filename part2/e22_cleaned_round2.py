"""E22: a second improvement round on the cleaned files, against v10's model (the teammate's features in all three priors, `_tm_avg`), same folds as e21,
paired bootstrap by customer. Rows: one extra screened correction on one line (the cleaned files fill the missing parking, alarm and security fields, and
the emerging claim history is market-internal), the peril-level shrinkage n0, one extra column in the power 1.6 prior, and a log blend with v9's model.
usage: e22_cleaned_round2.py [ROW NAME ...]   (default: every row whose prior files exist)"""
import sys, os; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2

O, C = "work/p2", "work/clean/work/p2"
BASE = "_tm_p16+_tm_po+_tm_ex"


def prior(root, tag, line):
    ds = [pl.read_parquet(f"{root}/devperil{t}_{line}.parquet") for t in tag.split("+")]
    return ds[0].select("row_id").with_columns(**{c: pl.Series(np.mean([d[c].to_numpy() for d in ds], 0)) for c in ds[0].columns if c != "row_id"})


def dev(y, m): return 4 * (y * m ** -0.5 + m ** 0.5 - 2 * np.sqrt(y))   # unit Tweedie 1.5 deviance per row


def oof(root, tag, extra=None, n0=400):
    ys, out, cs = [], [], []
    for line in LINES:
        em = pl.read_parquet(f"{root}/{line}.parquet").filter(pl.col("split") == "train").join(prior(root, tag, line), on="row_id").sort("row_id")
        short = list(model2.SHORT[line]) + ([extra[1]] if extra and extra[0] == line else [])
        y = em["y"].to_numpy(); o = np.zeros(len(y))
        for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
            o[vai] = model2.pipeline(em[tri], em[vai], n0_level=n0, short=short, score_is_train=True)
        ys.append(y); out.append(o); cs.append(em["customer_id"].to_numpy())
    return np.concatenate(ys), np.concatenate(out), np.concatenate(cs)


def spec(cols, perils=None): return {"cols": cols, "perils": perils}


RUNS = []
for line, cands in {"motor": [("overnight_parking", ["theft"]), ("overnight_parking", None), ("vehicle_age", None), ("pol_nclaims", None), ("cust_nclaims", None),
                              ("renewal_count", None), ("tenure_years", None), ("channel", None)],
                    "buildings": [("smoke_alarms", ["fire"]), ("smoke_alarms", None), ("renewal_count", None), ("pol_nclaims", None), ("cust_nclaims", None),
                                  ("tenure_years", None), ("channel", None)],
                    "contents": [("security_level", ["theft"]), ("high_value_items", ["theft"]), ("high_value_items", None), ("renewal_count", None),
                                 ("pol_nclaims", None), ("cust_nclaims", None), ("tenure_years", None), ("channel", None)]}.items():
    for col, per in cands:
        RUNS.append((f"{line} correction {col}" + (f" on {'+'.join(per)}" if per else ""), dict(tag=BASE, extra=(line, spec([col], per)))))
for n0 in (200, 800, 1600): RUNS.append((f"n0 {n0}", dict(tag=BASE, n0=n0)))
for t, col in (("_ch", "channel"), ("_pm", "payment_method"), ("_dq", "days_quote_to_inception"), ("_sm", "start_month"), ("_te", "tenure_years"),
               ("_nl", "n_lines"), ("_mk", "all four marketing columns"), ("_r350", "350 rounds (600)"), ("_r1000", "1000 rounds (600)")):
    RUNS.append((f"prior + {col}", dict(tag=f"{t}+_tm_po+_tm_ex")))
RUNS = [r for r in RUNS if (not sys.argv[1:] or r[0] in sys.argv[1:]) and os.path.exists(f"{C}/devperil{r[1]['tag'].split('+')[0]}_motor.parquet")]

if __name__ == "__main__":
    Y, A, G = oof(C, BASE)
    u, g = np.unique(G, return_inverse=True); dA = np.bincount(g, dev(Y, A)); d0 = np.bincount(g, dev(Y, np.full(len(Y), Y.mean())))

    def compare(name, B):
        dB = np.bincount(g, dev(Y, B)); rng = np.random.default_rng(0)
        diff = np.array([(dA[i].sum() - dB[i].sum()) / d0[i].sum() for i in (rng.integers(0, len(u), len(u)) for _ in range(2000))])
        print(f"{name:44s} D2 {1 - dB.sum() / d0.sum():.5f}  gain over v10 model {(dA.sum() - dB.sum()) / d0.sum():+.5f}  sd {diff.std():.5f}  P(gain>0) {(diff > 0).mean():.3f}", flush=True)

    print(f"{'v10 model (cleaned, _tm_avg)':44s} D2 {1 - dA.sum() / d0.sum():.5f}", flush=True)
    if not sys.argv[1:]:
        _, V9, _ = oof(O, "_x_p16+_v_po+_v_ex")
        for w in (0.0, 0.5):
            compare(f"log blend, weight {w} on v9's model", np.exp(w * np.log(V9) + (1 - w) * np.log(A)))
    for name, kw in RUNS:
        compare(name, oof(C, **kw)[1])
