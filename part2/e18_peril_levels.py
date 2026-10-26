"""E18: two new ways to set the peril levels, through the final pipeline (model2.pipeline with level_fn), 5 folds by customer shared by the three lines.

fs: split each peril level into frequency and severity and shrink them separately. Severity ratio S_p = emerging mean claim / developed mean claim (capped),
    frequency ratio F_p = k_p / S_p; log k = log F_line + c_f (log F_p - log F_line) + log S_line + c_s (log S_p - log S_line), c = n / (n + n0).
    Claim counts are steadier than claim sizes, so n0_f can be smaller than n0_s; n0_f = n0_s = 400 is the current model.
pool: perils that two lines share (escape_of_water, flood, accidental_damage in buildings and contents; theft in motor and contents) are shrunk toward the
    pooled relative level of both lines (weight N / (N + n0_p)) instead of toward 1 relative to the line level.
"""
import sys, zlib; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import *
import model2

SHARED = {"escape_of_water": ("buildings", "contents"), "flood": ("buildings", "contents"), "accidental_damage": ("buildings", "contents"), "theft": ("motor", "contents")}
data, fold = {}, {}
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devperil_v_avg_{line}.parquet"), on="row_id")
    data[line] = em; fold[line] = np.array([zlib.crc32(c.encode()) % 5 for c in em["customer_id"].to_list()])
dev_sev = {}
for line in LINES:
    dv = load(line, "dev").filter(pl.col("split") == "train"); dev_sev[line] = {}
    for p in model2.peril_cols(data[line]):
        yc, lf = cap_target(dv[f"y_{p}"].to_numpy(), 0.995); dev_sev[line][p] = (yc.sum() * lf, dv[f"n_{p}"].sum())


def stats(em, perils):
    base = {p: (np.exp(em[f"lrp_{p}"].to_numpy()) * em["exposure"].to_numpy() * em[f"compk_{p}"].to_numpy()).sum() for p in perils}
    kline = sum(em[f"y_{p}"].sum() for p in perils) / sum(base.values()); s = {}
    for p in perils:
        yc, lf = cap_target(em[f"y_{p}"].to_numpy(), 0.995); s[p] = (yc.sum() * lf, base[p], em[f"n_{p}"].sum())
    return kline, s


def fs_fn(line, n0f, n0s):
    def f(train, perils, base_t, kline, mult):
        _, s = stats(train, perils); out = {}
        Se = sum(v[0] for v in s.values()) / sum(v[2] for v in s.values()); Sd = sum(v[0] for v in dev_sev[line].values()) / sum(v[1] for v in dev_sev[line].values())
        Sl = Se / Sd; Fl = kline / Sl
        for p in perils:
            cost, b, n = s[p]; kp = cost / b; Sp = (cost / max(n, 1)) / (dev_sev[line][p][0] / dev_sev[line][p][1]); Fp = kp / Sp
            out[p] = np.exp(np.log(Fl) + n / (n + n0f) * (np.log(Fp) - np.log(Fl)) + np.log(Sl) + n / (n + n0s) * (np.log(Sp) - np.log(Sl)))
        return out
    return f


def pool_fn(line, k, n0p):
    other = {}   # fold-train stats of the other lines
    for l in LINES:
        if l != line: other[l] = stats(data[l].filter(pl.Series(fold[l] != k)), model2.peril_cols(data[l]))

    def f(train, perils, base_t, kline, mult):
        _, s = stats(train, perils); out = dict(mult)
        for p in perils:
            if p not in SHARED or line not in SHARED[p]: continue
            l2 = [l for l in SHARED[p] if l != line][0]; k2, s2 = other[l2]
            cost, b, n = s[p]; c2, b2, n2 = s2[p]
            r_pool = (cost + c2) / (kline * b + k2 * b2); N = n + n2; t = np.log(kline) + N / (N + n0p) * np.log(r_pool)
            out[p] = np.exp(t + n / (n + 400) * (np.log(cost / b) - t))
        return out
    return f


VARS = {"current (n0 400)": lambda line, k: None}
for n0f, n0s in ((100, 400), (100, 1000), (200, 1000), (400, 1000), (50, 2000)): VARS[f"fs n0_f {n0f} n0_s {n0s}"] = (lambda a, b: lambda line, k: fs_fn(line, a, b))(n0f, n0s)
for n0p in (100, 400, 1000): VARS[f"pool n0_p {n0p}"] = (lambda a: lambda line, k: pool_fn(line, k, a))(n0p)
for name, mk in VARS.items():
    ys, out, per = [], [], {}
    for line in LINES:
        em = data[line]; y = em["y"].to_numpy(); o = np.zeros(len(y))
        for k in range(5):
            tr, va = em.filter(pl.Series(fold[line] != k)), em.filter(pl.Series(fold[line] == k))
            o[fold[line] == k] = model2.pipeline(tr, va, short=model2.SHORT[line], score_is_train=True, level_fn=mk(line, k))
        ys.append(y); out.append(o); per[line] = round(d2(y, o), 4)
    print(f"{name:26s}", per, "pooled", round(d2(np.concatenate(ys), np.concatenate(out)), 4), flush=True)
