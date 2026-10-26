"""E19: large-loss cap with the load spread over the whole line instead of the peril (the per-peril cap of model2.pipeline puts its load back on the same
peril, so it does not change the levels), and corrections on voluntary excess or a broad candidate list. Same folds as e10."""
import sys; sys.path.insert(0,"part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2
def mk(q):
    def f(train, perils, base_t, kline, mult):
        caps = {p: cap_target(train[f"y_{p}"].to_numpy(), q) for p in perils}
        LF = sum(train[f"y_{p}"].sum() for p in perils) / sum(c[0].sum() for c in caps.values()); out = {}
        for p in perils:
            kp = caps[p][0].sum() * LF / base_t[p].sum(); n = train[f"n_{p}"].sum(); c = n / (n + 400)
            out[p] = np.exp(np.log(kline) + c * (np.log(kp) - np.log(kline)))
        return out
    return f
for q in (None, 0.999, 0.995, 0.99, 0.98):
    ys, out, per = [], [], {}
    for line in LINES:
        em = load(line,"em").filter(pl.col("split")=="train").join(pl.read_parquet(f"work/p2/devperil_v_avg_{line}.parquet"), on="row_id")
        y = em["y"].to_numpy(); o = np.zeros(len(y))
        for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
            o[vai] = model2.pipeline(em[tri], em[vai], short=model2.SHORT[line], score_is_train=True, level_fn=mk(q) if q else None)
        ys.append(y); out.append(o); per[line] = round(d2(y,o),4)
    print("line-level load, cap", q, per, "pooled", round(d2(np.concatenate(ys), np.concatenate(out)),4), flush=True)
S = model2.SHORT
V = {"final": S,
     "+ voluntary_excess": {l: S[l] + [{"cols": ["voluntary_excess"]}] for l in LINES},
     "+ excess, broad candidate list": {l: S[l] + [{"cols": ["voluntary_excess", "channel", "payment_method", "cover_type" if l == "motor" else "occupancy" if l == "buildings" else "tenure", "urban_density", "marital_status"]}] for l in LINES}}
for name, sh in V.items():
    ys, out, per = [], [], {}
    for line in LINES:
        em = load(line,"em").filter(pl.col("split")=="train").join(pl.read_parquet(f"work/p2/devperil_v_avg_{line}.parquet"), on="row_id")
        y = em["y"].to_numpy(); o = np.zeros(len(y))
        for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
            o[vai] = model2.pipeline(em[tri], em[vai], short=sh[line], score_is_train=True)
        ys.append(y); out.append(o); per[line] = round(d2(y,o),4)
    print(f"{name:32s}", per, "pooled", round(d2(np.concatenate(ys), np.concatenate(out)),4), flush=True)
