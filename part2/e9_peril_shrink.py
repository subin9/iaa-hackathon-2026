"""E9: peril-level calibration of the NB-aware per-peril prior with credibility shrinkage toward the line level.
log k_p* = log k_line + c_p (log k_p - log k_line), c_p = n_p / (n_p + N0). 5-fold CV grouped by customer, pooled D2."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
TAGP = sys.argv[1] if len(sys.argv) > 1 else "_nb"
N0S = [0, 50, 150, 400, 1000, 1e9]
res = {n0: [] for n0 in N0S}; ys = []; per = {n0: {} for n0 in N0S}
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil{TAGP}_{line}.parquet"), on="row_id")
    perils = sorted(c[4:] for c in em.columns if c.startswith("lrp_")); grp = em["customer_id"].to_numpy(); ye = em["y"].to_numpy(); ys.append(ye)
    capped = {}; 
    for p in perils: capped[p] = cap_target(em[f"y_{p}"].to_numpy(), 0.995)       # (capped cost, load) per peril
    base = {p: np.exp(em[f"lrp_{p}"].to_numpy()) * em["exposure"].to_numpy() * em[f"compk_{p}"].to_numpy() for p in perils}   # prior mean on the reported basis, includes the cap load
    npc = {p: em[f"n_{p}"].to_numpy() for p in perils}
    out = {n0: np.zeros(len(ye)) for n0 in N0S}
    for tri, vai in GroupKFold(5).split(em, ye, grp):
        # line level from the total reported cost (peril sum of the prior)
        tot_prior = sum(base[p][tri].sum() for p in perils); kline = sum(em[f"y_{p}"].to_numpy()[tri].sum() for p in perils) / tot_prior
        for n0 in N0S:
            pred = np.zeros(len(vai))
            for p in perils:
                yc, lf = capped[p]; kp = (yc[tri].sum() * lf) / base[p][tri].sum()   # peril level estimated on capped cost with the cap load put back
                n = npc[p][tri].sum(); c = n / (n + n0) if n0 < 1e8 else 0.0
                pred += np.exp(np.log(kline) + c * (np.log(kp) - np.log(kline))) * base[p][vai]
            out[n0][vai] = pred
    for n0 in N0S: res[n0].append(out[n0]); per[n0][line] = round(d2(ye, out[n0]), 4)
for n0 in N0S: print(f"N0={n0:>8}", per[n0], "pooled", round(d2(np.concatenate(ys), np.concatenate(res[n0])), 4))
