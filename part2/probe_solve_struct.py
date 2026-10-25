"""Solve the segment probes of one base submission under a multiplicative structure.

The public deviance is separable by cell, Dev(c) = sum_k 4 f T_k [m*_k c_k^-1/2 + c_k^1/2], with T_k = mu_k^1/2 summed over the test rows of cell k and
c_k the factor a probe applies (m*_k is the best factor of the cell, unknown). The cells are crossed segments, so there are more cells than probes;
the best factor of a cell is therefore modelled as a product: m*_k = M[base segment of k] x Gd^[motor new business, direct channel] x Gm^[motor, male]
x Ga^[buildings, age band 35-49]. Seven parameters, seven probes. The rounding of the score (5 digits) is propagated into a standard error per parameter.

usage: probe_solve_struct.py PROBES_JSON   (list of {"file": csv, "public": score}; the first item is the base submission itself)
"""
import sys, json
import numpy as np, polars as pl
from scipy.optimize import least_squares
sys.path.insert(0, "part2")
import segments

F = 1.0 / 3.0
PARAMS = ["motor_nb", "buildings_nb", "contents_nb", "renewal", "direct_nb_motor", "male_motor", "age3549_buildings"]


def structure(d: pl.DataFrame):
    line, nb = d["line"].to_numpy(), d["nb"].to_numpy()
    seg = np.where(nb == 0, 3, np.select([line == "motor", line == "buildings"], [0, 1], 2))
    flags = np.stack([(line == "motor") & (nb == 1) & (d["channel"].to_numpy() == "direct"),
                      (line == "motor") & (d["gender"].to_numpy() == "M"),
                      (line == "buildings") & (d["age"].to_numpy() == "35-49")], 1).astype(float)
    return seg, flags


def mstar_rows(logp, seg, flags):
    return np.exp(logp[:4][seg] + flags @ logp[4:])


def dev(mstar, T, c):
    return float((4 * F * T * (mstar / np.sqrt(c) + np.sqrt(c))).sum())


def solve(mu, cs, public, seg, flags):
    """cs[i] = factor vector of probe i (cs[0] = ones, the base); public[i] = its score. Returns (log params, log se, max residual, T)."""
    T = np.sqrt(mu)

    def model(logp):
        ms = mstar_rows(logp, seg, flags); dev0 = dev(ms, T, cs[0]) / (1 - public[0])
        return np.array([1 - dev(ms, T, c) / dev0 for c in cs[1:]])

    resid = lambda logp: model(logp) - np.array(public[1:])
    fit = least_squares(resid, np.zeros(7), xtol=1e-12, ftol=1e-14, gtol=1e-14)
    J = fit.jac; cov = np.linalg.inv(J.T @ J) * (2.9e-6) ** 2   # sd of a uniform rounding error at 5 digits
    return fit.x, np.sqrt(np.diag(cov)), float(np.abs(resid(fit.x)).max()), T


def predict(mu, logp, seg, flags, c, public0, cs0):
    T = np.sqrt(mu); ms = mstar_rows(logp, seg, flags); dev0 = dev(ms, T, cs0) / (1 - public0)
    return 1 - dev(ms, T, c) / dev0


if __name__ == "__main__":
    pr = json.load(open(sys.argv[1]))
    base = pl.read_csv(pr[0]["file"]); d = segments.test_frame(base); seg, flags = structure(d)
    mu = d["prediction"].to_numpy()
    cs = [np.ones(len(mu))]
    for p in pr[1:]:
        q = d.select("row_id").join(pl.read_csv(p["file"]), on="row_id", how="left")["prediction"].to_numpy(); cs.append(q / mu)
    x, se, err, T = solve(mu, cs, [p["public"] for p in pr], seg, flags)
    print("max |residual|", f"{err:.1e}")
    for n, v, s in zip(PARAMS, np.exp(x), se): print(f"  {n:20s} m* = {v:.3f}  (log se {s:.3f})")
    ms = mstar_rows(x, seg, flags)
    for name, c in [("m*", ms), ("sqrt(m*)", np.sqrt(ms))]:
        print(f"  predicted public D2 at {name}:", round(predict(mu, x, seg, flags, c, pr[0]["public"], cs[0]), 5))
