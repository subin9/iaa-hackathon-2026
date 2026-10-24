"""E12: experience rating on renewals. For 2024 rows whose policy also has a 2023 row: factor = 1 + Z (A/E - 1), Z = E / (E + K),
A the capped 2023 cost of the policy, E its expected cost (pipeline prediction). D2 of the 2024 rows, 5-fold CV grouped by customer."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
from lib import *
import model2
TAGP = "_v_avg"; SHORT = {"motor": ["gender"], "buildings": ["policyholder_age_band"], "contents": []}
Ks = [1e9, 3000, 1000, 300, 100]
tot = {K: [] for K in Ks}; ys = []
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil{TAGP}_{line}.parquet"), on="row_id")
    ye = em["y"].to_numpy(); o = np.zeros(len(ye))
    for tri, vai in GroupKFold(5).split(em, ye, em["customer_id"].to_numpy()):
        o[vai] = model2.pipeline(em[tri], em[vai], short=SHORT[line], score_is_train=True)
    em = em.with_columns(mu=pl.Series(o))
    ycap, lf = cap_target(ye, 0.99)
    h = em.with_columns(ycap=pl.Series(ycap)).filter(pl.col("year") == 2023).group_by("policy_id").agg(A=pl.col("ycap").sum(), E=pl.col("mu").sum())
    d = em.filter(pl.col("year") == 2024).join(h, on="policy_id", how="left"); has = d["E"].is_not_null().to_numpy()
    y24 = d["y"].to_numpy(); mu24 = d["mu"].to_numpy(); A = d["A"].fill_null(0).to_numpy(); E = d["E"].fill_null(0).to_numpy(); ys.append(y24)
    for K in Ks:
        Z = E / (E + K); f = np.where(has, 1 + Z * (A / np.maximum(E, 1e-9) - 1), 1.0); f = np.clip(f, 0.5, 3.0)
        p = mu24 * f; tot[K].append(p)
    print(line, "2024 rows", len(y24), "with 2023 history", int(has.sum()), {K: round(d2(y24, mu24 * np.clip(np.where(has, 1 + E / (E + K) * (A / np.maximum(E, 1e-9) - 1), 1.0), 0.5, 3.0)), 4) for K in Ks}, flush=True)
Y = np.concatenate(ys); print("pooled 2024 rows", {K: round(d2(Y, np.concatenate(tot[K])), 4) for K in Ks})
