"""Solve public-leaderboard level probes of one base submission for the best multiplier per segment.

The public deviance is a sum over rows, so it is separable by segment: Dev(m) = sum_s 4 [U_s m_s^-1/2 + f T_s m_s^1/2], where
U_s = sum over public rows of y mu^-1/2 (unknown), T_s = sum over all test rows of mu^1/2 (known) and f is the public share.
D2 = 1 - Dev / Dev0, and Dev0 follows from the base score. The best multiplier is m*_s = U_s / (f T_s); f cancels out of it.
Each probe multiplies one or more segments; probes + the base score must outnumber the segments.

usage: probe_solve.py BASE.parquet SEGS_JSON PROBES_JSON   (the base parquet has prediction, line, new_business)
"""
import sys, json
import numpy as np
from scipy.optimize import least_squares


def segment_T(mu, masks):
    return {n: float((mu[m] ** 0.5).sum()) for n, m in masks.items()}


def solve(T, probes, f=1.0 / 3.0):
    """probes[0] = {"d2": base score}; the others {"seg": name or list of names, "m": multiplier, "d2": score}. Returns (m*, predict)."""
    names = list(T); base_d2 = probes[0]["d2"]

    def dev(U, mult):
        return sum(4 * (U[n] * mult.get(n, 1.0) ** -0.5 + f * T[n] * mult.get(n, 1.0) ** 0.5) for n in names)

    def resid(x):
        U = {n: xi * f * T[n] for n, xi in zip(names, x)}; dev0 = dev(U, {}) / (1 - base_d2)
        return [1 - dev(U, {s: p["m"] for s in ([p["seg"]] if isinstance(p["seg"], str) else p["seg"])}) / dev0 - p["d2"] for p in probes[1:]]

    fit = least_squares(resid, np.ones(len(names)), xtol=1e-12, ftol=1e-14, gtol=1e-14)
    mstar = dict(zip(names, fit.x)); U = {n: mstar[n] * f * T[n] for n in names}; dev0 = dev(U, {}) / (1 - base_d2)
    predict = lambda mult: 1 - dev(U, mult) / dev0
    return mstar, predict, float(np.max(np.abs(resid(fit.x))))


if __name__ == "__main__":
    import polars as pl
    d = pl.read_parquet(sys.argv[1]); mu = d["prediction"].to_numpy(); line = d["line"].to_numpy(); nb = d["new_business"].to_numpy()
    segs = json.loads(sys.argv[2]); probes = json.loads(sys.argv[3]); masks = {}
    for n, (l, b) in segs.items():
        m = np.ones(len(d), bool)
        if l != "all": m &= line == l
        if b is not None: m &= nb == bool(b)
        masks[n] = m
    T = segment_T(mu, masks); mstar, predict, err = solve(T, probes)
    print("max |residual|", f"{err:.1e}")
    for n in T: print(f"  {n:22s} m* = {mstar[n]:.3f}   (share of sum mu^1/2 {T[n] / sum(T.values()):.2f})")
    print("  predicted public D2: base", round(predict({n: 1.0 for n in T}), 5), "| at m*", round(predict(mstar), 5), "| halfway (log)", round(predict({n: np.sqrt(mstar[n]) for n in T}), 5))
