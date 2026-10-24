"""E5: peril-level A/E of the developed prior on emerging rows (by year), then CV of peril-level versus line-level calibration."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_width_chars(160)
rows = []; ys = []; oof_line, oof_peril = [], []
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil_{line}.parquet"), on="row_id").join(pl.read_parquet(f"work/p2/devprior_{line}.parquet"), on="row_id")
    perils = sorted(c[4:] for c in em.columns if c.startswith("lrp_")); yr = em["year"].to_numpy(); grp = em["customer_id"].to_numpy()
    base = {p: np.exp(em[f"lrp_{p}"].to_numpy()) * em["exposure"].to_numpy() * em[f"compk_{p}"].to_numpy() for p in perils}
    ypr = {p: em[f"y_{p}"].to_numpy() for p in perils}
    for p in perils:
        r = dict(line=line, peril=p, n=int(em[f"n_{p}"].sum()))
        for y in (2023, 2024): k = yr == y; r[f"AE{y}"] = round(ypr[p][k].sum() / base[p][k].sum(), 3)
        r["AE_all"] = round(ypr[p].sum() / base[p].sum(), 3); rows.append(r)
    ye = em["y"].to_numpy(); ys.append(ye); ol, op = np.zeros(len(ye)), np.zeros(len(ye))
    ult = {p: np.exp(em[f"lrp_{p}"].to_numpy()) * em["exposure"].to_numpy() for p in perils}      # ultimate-basis prior per peril
    comp = em["completion"].to_numpy(); lin = np.exp(em["lr_dev"].to_numpy()) * em["exposure"].to_numpy()
    for tri, vai in GroupKFold(5).split(em, ye, grp):
        kl = ye[tri].sum() / (lin[tri] * comp[tri]).sum(); ol[vai] = kl * lin[vai] * comp[vai]
        kp = {p: ypr[p][tri].sum() / base[p][tri].sum() for p in perils}; op[vai] = sum(kp[p] * base[p][vai] for p in perils)
    oof_line.append(ol); oof_peril.append(op)
    print(line, "D2 line-level", round(d2(ye, ol), 4), "peril-level", round(d2(ye, op), 4), flush=True)
print(pl.DataFrame(rows))
Y = np.concatenate(ys); print("pooled line-level", round(d2(Y, np.concatenate(oof_line)), 4), "peril-level", round(d2(Y, np.concatenate(oof_peril)), 4))
