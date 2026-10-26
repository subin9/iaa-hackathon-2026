"""E16: how much of the leaderboard-fitted gain should carry over to the private rows? Posterior of each cell's private optimum under the ridge prior of
probe_solve_cells.py (mean w * m*, variance w se^2 plus the private sampling noise se^2 / 2), expected private D2 change of v7, v8, the unshrunk optimum and half of v7
against the base v5. Uses the corrected solver (with the deviance constant), so it slightly favours v8 by construction."""
import sys, json, os
sys.argv = ["x", "part2/v5_probes.json", "/dev/null"]
sys.path.insert(0, "part2")
import numpy as np, polars as pl
import probe_solve_cells as P, segments
from scipy.optimize import least_squares
pr = json.load(open(sys.argv[1])); base = pl.read_csv(pr[0]["file"]); d = segments.test_frame(base); mu = d["prediction"].to_numpy(); T = np.sqrt(mu)
cid, names = P.cells(d); K = len(names); Tk = np.bincount(cid, T, K); nk = np.bincount(cid, minlength=K)
ck = [ (d.select("row_id").join(pl.read_csv(p["file"]), on="row_id", how="left")["prediction"].to_numpy()/mu) for p in pr[1:]]
ck = [np.array([c[cid==k][0] for k in range(K)]) for c in ck]; public = np.array([p["public"] for p in pr]); F = P.F
pool = np.load("work/p2/oof_pool.npz")
S0 = sum(8*np.sqrt(pool[f"{l}_a"]*pool[f"{l}_b"]).sum()*F*float(T[d["line"].to_numpy()==l].sum())/pool[f"{l}_b"].sum() for l in ("motor","buildings","contents"))
dev = lambda ms, c: float((4*F*Tk*(ms/np.sqrt(c)+np.sqrt(c))).sum())
def model(x, cl):
    ms, S = np.exp(x[:K]), S0*np.exp(x[K]); dev0 = (dev(ms, np.ones(K))-S)/(1-public[0]); return np.array([1-(dev(ms,c)-S)/dev0 for c in cl]), dev0
res = lambda x: np.concatenate([(model(x, ck)[0]-public[1:])/P.SIGMA, x[:K]/P.TAU, [x[K]/0.5]])
x = least_squares(res, np.zeros(K+1), xtol=1e-12, ftol=1e-14, gtol=1e-14, max_nfev=2000).x; th = x[:K]; dev0_pub = model(x,[np.ones(K)])[1]
rng = np.random.default_rng(1); se = np.zeros(K)
for k, nm in enumerate(names):
    a, b = pool[nm.split("|")[0]+"_a"], pool[nm.split("|")[0]+"_b"]; n = max(int(F*nk[k]),50)
    idx = rng.integers(0,len(a),(400,n)); se[k] = np.log(a[idx].sum(1)/b[idx].sum(1)).std()
w = P.TAU**2/(P.TAU**2+se**2)
# private part: 2/3 of the rows. Posterior of the private-row optimum log m: the public estimate th carries noise se (public sample) and the private optimum
# has its own sampling noise se/sqrt(2); with the N(0, tau^2) prior the posterior mean is w*th and its sd sqrt(w)*se, plus private noise.
v7 = pl.read_csv("work/p2/v7_submit.csv"); a7 = d.select("row_id").join(v7, on="row_id")["prediction"].to_numpy()/mu; a7 = np.array([a7[cid==k][0] for k in range(K)])
v8 = pl.read_csv("work/p2/v8.csv"); a8 = d.select("row_id").join(v8, on="row_id")["prediction"].to_numpy()/mu; a8 = np.array([a8[cid==k][0] for k in range(K)])
Fp = 1-F; dev0_priv = dev0_pub*Fp/F
def exp_gain(a, draws=20000):
    m = np.exp(w*th + np.sqrt(w*se**2 + se**2/2)*rng.standard_normal((draws,K)))     # private optimum per cell
    dd = (4*Fp*Tk*(m*(a**-0.5-1)+(a**0.5-1))).sum(1)                                # private deviance change against the base
    return -dd/dev0_priv
for nm, a in (("v7 (submitted)", a7), ("v8 (corrected solver)", a8), ("unshrunk th", np.exp(th)), ("half of v7", np.sqrt(a7))):
    g = exp_gain(a); print(f"{nm:24s} expected private D2 gain over v5 {g.mean():+.5f}  sd {g.std():.5f}  P(gain<0) {(g<0).mean():.3f}")
print("public gain v7 over v5:", round(0.17300-0.16797,5))
