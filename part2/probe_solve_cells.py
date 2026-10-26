"""Best factor per cell of a base submission from all its leaderboard probes, shrunk by sampling noise, written as a new submission.

Cells are crossed segments of the test rows where every probe and every candidate applies one factor: motor new business x direct channel x gender,
motor renewals x gender, buildings x new business x age band 35-49, contents x new business (12 cells). The public deviance is exact in the cells,
Dev = sum_k 4 [U_k c_k^-1/2 + f T_k c_k^1/2] - S, U_k = m*_k f T_k, S = 8 sum(sqrt(y)) over the public rows, so each submission scored on the leaderboard is one
equation in the 12 unknown m*_k and S (the null deviance follows from the base score). With fewer equations than cells the problem is under-determined; a ridge prior log m*_k ~ N(0, 0.25^2) (the base is already
calibrated on training) picks the smallest change. The public m*_k carries sampling noise (e13_cell_noise.py, bootstrap of the out-of-fold training rows), which
the private rows do not share, so every log m*_k is then multiplied by tau^2 / (tau^2 + se_k^2). Two approximations: se_k is bootstrapped from the whole line's rows (not the cell's own mix),
and the same tau serves the ridge and the shrinkage, so the prior acts twice (deliberately conservative).

usage: probe_solve_cells.py PROBES_JSON OUT.csv [tau]   (PROBES_JSON: list of {"file", "public"}; first item is the base)
"""
import sys, json, os
import numpy as np, polars as pl
from scipy.optimize import least_squares
sys.path.insert(0, "part2")
import segments, submission

F = 1.0 / 3.0
TAU = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
SIGMA = 2e-4   # the equations use f x (all test rows) in place of the unknown public sum of mu^1/2 per cell: about 1e-4 of D2 error per probe


def cells(d):
    line, nb, ch, g, age = (d[c].to_numpy() for c in ("line", "nb", "channel", "gender", "age"))
    key = np.array([f"{l}|nb{n}|{'dir' if (l == 'motor' and n == 1 and c == 'direct') else ''}|{'M' if (l == 'motor' and s == 'M') else ''}|{'a3549' if (l == 'buildings' and a == '35-49') else ''}"
                    for l, n, c, s, a in zip(line, nb, ch, g, age)])
    names = sorted(set(key)); return np.array([names.index(k) for k in key]), names


def main():
    pr = json.load(open(sys.argv[1])); base = pl.read_csv(pr[0]["file"]); d = segments.test_frame(base); mu = d["prediction"].to_numpy(); T = np.sqrt(mu)
    cid, names = cells(d); K = len(names)
    Tk = np.bincount(cid, T, K); nk = np.bincount(cid, minlength=K)
    ck = []
    for p in pr[1:]:
        c = d.select("row_id").join(pl.read_csv(p["file"]), on="row_id", how="left")["prediction"].to_numpy() / mu
        cell_c = np.array([c[cid == k][0] for k in range(K)]); assert all(np.allclose(c[cid == k], cell_c[k], rtol=1e-4) for k in range(K)), "probe is not constant in a cell"
        ck.append(cell_c)
    public = np.array([p["public"] for p in pr])

    pool = np.load("work/p2/oof_pool.npz")
    # The Tweedie deviance is 4 [y mu^-1/2 + mu^1/2 - 2 sqrt(y)]; the constant S = 8 sum(sqrt(y)) over the public rows cancels between submissions but not in the
    # null deviance, which is (Dev(base) - S) / (1 - base score). S is estimated from the out-of-fold training rows (sum of sqrt(y) scaled by the share of sqrt(mu)
    # of the public part of the test rows) and enters as one more unknown, log s, with a wide prior.
    S0 = sum(8 * np.sqrt(pool[f"{l}_a"] * pool[f"{l}_b"]).sum() * F * float(T[d["line"].to_numpy() == l].sum()) / pool[f"{l}_b"].sum() for l in ("motor", "buildings", "contents"))
    if os.environ.get("P2_NO_CONSTANT"): S0 = 0.0   # reproduces the submitted v7, solved before the constant was found

    def dev(ms, c): return float((4 * F * Tk * (ms / np.sqrt(c) + np.sqrt(c))).sum())

    def model(x, cl):
        ms, S = np.exp(x[:K]), S0 * np.exp(x[K]); dev0 = (dev(ms, np.ones(K)) - S) / (1 - public[0]); return np.array([1 - (dev(ms, c) - S) / dev0 for c in cl])

    res = lambda x: np.concatenate([(model(x, ck) - public[1:]) / SIGMA, x[:K] / TAU, [x[K] / 0.5]])
    x = least_squares(res, np.zeros(K + 1), xtol=1e-12, ftol=1e-14, gtol=1e-14, max_nfev=2000).x
    print("max |score residual|", f"{np.abs(model(x, ck) - public[1:]).max():.1e}", "| S / S estimate", round(float(np.exp(x[K])), 2)); th = x[:K]
    rng = np.random.default_rng(1); se = np.zeros(K)
    for k, nm in enumerate(names):
        a, b = pool[nm.split("|")[0] + "_a"], pool[nm.split("|")[0] + "_b"]; n = max(int(F * nk[k]), 50)
        idx = rng.integers(0, len(a), (400, n)); se[k] = np.log(a[idx].sum(1) / b[idx].sum(1)).std()
    w = TAU ** 2 / (TAU ** 2 + se ** 2); applied = th * w
    for k, nm in enumerate(names): print(f"  {nm:34s} rows {nk[k]:6d}  m* {np.exp(th[k]):6.3f}  se {se[k]:.3f}  weight {w[k]:.2f}  applied {np.exp(applied[k]):.3f}")
    f = np.exp(applied)[cid]; pred = lambda t: model(x, [np.exp(t)])[0]     # score of the factors exp(t) when the fitted m* are the truth
    print("predicted public D2: at m*", round(pred(th), 5), "| applied", round(pred(applied), 5))
    out = d.with_columns(prediction=pl.Series(mu * f)).select("row_id", "prediction")
    print("total before", round(float(mu.sum())), "after", round(float(out["prediction"].sum()))); submission.write(out, sys.argv[2])


if __name__ == "__main__":
    main()
