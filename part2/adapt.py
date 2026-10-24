"""Market adaptation by screened corrections: a ridge Tweedie GLM on emerging rows with the developed prior as offset.

Candidate factors are screened with a robust (sandwich) score test, so no refit is needed to rank them and no dispersion
assumption is made; the best one that passes the threshold enters, the GLM is refitted with a ridge penalty (a credibility
weight), and the screen repeats. The factors that enter are the "what changed" list of the report.
"""
import numpy as np, polars as pl
from scipy.stats import chi2

P = 1.5


def block(s: pl.Series, min_rows=300, bins=5):
    """One-hot block for one column: categories (rare levels pooled with the reference), numerics cut at quantiles, NA own level."""
    if s.dtype.is_numeric() and not s.dtype == pl.Boolean and s.n_unique() > 8:
        v = s.to_numpy().astype(float); e = np.unique(np.quantile(v[~np.isnan(v)], np.linspace(0, 1, bins + 1)[1:-1]))
        lab = np.where(np.isnan(v), "NA", np.char.add("q", np.searchsorted(e, np.nan_to_num(v, nan=0)).astype(str)))
        spec = ("num", e)
    else:
        lab = s.cast(pl.Utf8).fill_null("NA").to_numpy().astype(str); spec = ("cat", None)
    lv, cnt = np.unique(lab, return_counts=True)
    lv = lv[cnt >= min_rows]
    ref = lv[np.argmax(cnt[cnt >= min_rows])] if len(lv) else None
    use = [x for x in lv if x != ref]
    return lab, use, ref, spec


def design(df: pl.DataFrame, cols, blocks=None):
    """Dense design matrix of one-hot blocks; blocks (levels fixed on the training rows) can be reused to encode other rows."""
    new = blocks is None; blocks = {} if new else blocks; mats, names, owner = [], [], []
    for c in cols:
        if new:
            lab, use, ref, spec = block(df[c]); blocks[c] = (use, ref, spec)
        else:
            use, ref, spec = blocks[c]
            s = df[c]
            if spec[0] == "num":
                v = s.to_numpy().astype(float); lab = np.where(np.isnan(v), "NA", np.char.add("q", np.searchsorted(spec[1], np.nan_to_num(v, nan=0)).astype(str)))
            else:
                lab = s.cast(pl.Utf8).fill_null("NA").to_numpy().astype(str)
        for lv in use:
            mats.append((lab == lv).astype(np.float64)); names.append(f"{c}={lv}"); owner.append(c)
    X = np.column_stack(mats) if mats else np.zeros((len(df), 0))
    return X, names, owner, blocks


def fit_glm(X, y, off, n0, iters=25, beta0=None):
    """Tweedie p=1.5 log-link IRLS with a ridge penalty on the slope coefficients (the intercept is free).
    The penalty is n0 claims' worth of information: a level with n claims is shrunk by about n / (n + n0)."""
    n, k = X.shape; A = np.column_stack([np.ones(n), X]); beta = np.zeros(k + 1) if beta0 is None else beta0.copy()
    nclaims = max(int((y > 0).sum()), 1)
    for _ in range(iters):
        eta = A @ beta + off; mu = np.exp(np.clip(eta, -30, 30))
        W = mu ** (2 - P); z = eta - off + (y - mu) / np.maximum(mu, 1e-12)
        pen = np.r_[0.0, np.full(k, n0 * W.sum() / nclaims)]
        H = A.T @ (A * W[:, None]) + np.diag(pen); new = np.linalg.solve(H, A.T @ (W * z))
        if np.max(np.abs(new - beta)) < 1e-6: beta = new; break
        beta = new
    return beta


def robust_score(Xb, y, mu):
    """Robust score statistic and df for adding the columns Xb to a model with fitted means mu."""
    r = (y - mu) * mu ** (1 - P); U = Xb.T @ r; V = (Xb * (r ** 2)[:, None]).T @ Xb
    k = Xb.shape[1]
    try:
        stat = float(U @ np.linalg.solve(V + 1e-9 * np.eye(k) * max(np.trace(V) / k, 1e-12), U))
    except np.linalg.LinAlgError:
        return 0.0, k
    return stat, k


class Adapter:
    """fit(df, y, off) on emerging rows; predict(df) returns the multiplicative correction exp(X b) (level included)."""
    def __init__(self, cands, alpha=0.02, ridge=100.0, max_steps=6, bonferroni=False):
        self.cands, self.alpha, self.ridge, self.max_steps, self.bonf = cands, alpha, ridge, max_steps, bonferroni

    def fit(self, df, y, off):
        self.chosen, self.log = [], []; self.blocks = {}
        Xall = {}; own = {}
        for c in self.cands:
            Xc, nm, ow, bl = design(df, [c]); Xall[c] = Xc; self.blocks[c] = bl[c]
        base = np.log(y.sum() / np.exp(off).sum()); mu = np.exp(off + base)
        beta, cur = np.array([base]), np.zeros((len(df), 0)); alpha_each = self.alpha / (max(len(self.cands), 1) if self.bonf else 1)
        for step in range(self.max_steps):
            best = None
            for c in self.cands:
                if c in self.chosen or Xall[c].shape[1] == 0: continue
                stat, k = robust_score(Xall[c], y, mu); p = chi2.sf(stat, k)
                if best is None or p < best[0]: best = (p, c, stat, k)
            if best is None or best[0] >= alpha_each: break
            self.chosen.append(best[1]); self.log.append((best[1], round(best[2], 1), best[3], best[0]))
            cur = np.column_stack([Xall[c] for c in self.chosen]); beta = fit_glm(cur, y, off, self.ridge)
            mu = np.exp(off + np.column_stack([np.ones(len(df)), cur]) @ beta)
        self.beta = beta if self.chosen else np.array([base]); self.names = []
        for c in self.chosen: self.names += [f"{c}={l}" for l in self.blocks[c][0]]
        return self

    def predict(self, df):
        n = len(df)
        if not self.chosen: return np.full(n, np.exp(self.beta[0]))
        X = np.column_stack([design(df, [c], {c: self.blocks[c]})[0] for c in self.chosen])
        return np.exp(np.column_stack([np.ones(n), X]) @ self.beta)

    def effects(self):
        return {nm: round(float(np.exp(b)), 3) for nm, b in zip(self.names, self.beta[1:])}
