"""Frequency x severity by peril.

Frequency: LightGBM Poisson per peril on claim counts, offset log(exposure x
count completion), so the model estimates ultimate frequency.
Severity: one LightGBM Gamma model per line on reported claims (capped per
peril), with peril as a feature, trended to the target year.
Each peril is then rebalanced so modelled cost matches reported cost after
cost completion, which absorbs the cap, late-reported severity and the
Poisson-Gamma product bias.
"""
import os
import numpy as np, polars as pl, lightgbm as lgb, pandas as pd
from common import load, to_pandas, align_categories, d2
from exp import codes

FREQ = dict(objective="poisson", learning_rate=0.05, num_leaves=15, min_data_in_leaf=2000,
            feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0,
            verbose=-1, num_threads=int(os.environ.get("NT", 6)))
SEV = dict(objective="gamma", learning_rate=0.05, num_leaves=7, min_data_in_leaf=500,
           feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0,
           verbose=-1, num_threads=int(os.environ.get("NT", 6)))
SEV_CAP = 0.995


def perils_of(df):
    return sorted(c[2:] for c in df.columns if c.startswith("n_") and c != "n_lines")


def sev_trend(claims_rows, p, cap, tr):
    """Log-linear severity trend per year for one peril, on capped claims.

    Years whose claim count is less than 95% reported are left out: their
    reported claims are the quick, small ones and would bend the trend down.
    """
    mature = tr.group_by("year").agg(c=(pl.col(f"compc_{p}") * pl.col("exposure")).sum() / pl.col("exposure").sum())
    keep = mature.filter(pl.col("c") > 0.95)["year"].to_list()
    g = claims_rows.filter((pl.col("peril") == p) & pl.col("year").is_in(keep)).group_by("year").agg(
        s=pl.col("net").clip(upper_bound=cap).mean()).sort("year")
    return np.polyfit(g["year"].to_numpy(), np.log(g["s"].to_numpy()), 1)[0] if g.height > 1 else 0.0


def fit_line(line, tr, claims, f_rounds=300, s_rounds=200, seed=0):
    X = codes(to_pandas(tr))
    perils = perils_of(tr)
    freq = {}
    for p in perils:
        n = tr[f"n_{p}"].to_numpy(); w = tr["exposure"].to_numpy() * tr[f"compc_{p}"].to_numpy()
        base = np.log(n.sum() / w.sum())
        m = lgb.train({**FREQ, "seed": seed}, lgb.Dataset(X, n, init_score=np.log(w) + base), f_rounds)
        freq[p] = (m, base)
    # severity: claims matched to training rows
    cr = claims.filter(pl.col("line") == line).join(
        tr.select("row_id", "policy_id", "period_start", "period_end", "year"), on="policy_id")
    cr = cr.filter(pl.col("loss_date").is_between(pl.col("period_start"), pl.col("period_end")) & (pl.col("status") != "repudiated"))
    caps = {p: cr.filter(pl.col("peril") == p)["net"].quantile(SEV_CAP) for p in perils}
    trend = {p: sev_trend(cr, p, caps[p], tr) for p in perils}
    cr = cr.with_columns(capv=pl.col("peril").replace_strict(caps, return_dtype=pl.Float64),
                         g=pl.col("peril").replace_strict(trend, return_dtype=pl.Float64))
    cr = cr.with_columns(s=pl.col("net").clip(upper_bound=pl.col("capv")))
    cr = cr.filter(pl.col("s") > 0)
    last = int(tr["year"].max())
    # put every claim at the last training year's level
    s_adj = (cr["s"] * np.exp(cr["g"] * (last - cr["year"]))).to_numpy()
    rows_idx = tr.select("row_id").with_row_index("i")
    ci = cr.select("row_id").join(rows_idx, on="row_id", how="left", maintain_order="left")["i"].to_numpy()
    Xs = X.iloc[ci].reset_index(drop=True).drop(columns=["year"])
    Xs["peril"] = pd.Categorical(cr["peril"].to_list(), categories=perils).codes
    ms = lgb.train({**SEV, "seed": seed}, lgb.Dataset(Xs, s_adj), s_rounds)
    model = dict(X=X, perils=perils, freq=freq, sev=ms, trend=trend, last=last, k={})
    # rebalance each peril against reported cost
    parts = raw_parts(model, tr, year_shift=0, Xready=X)
    for p in perils:
        exp_rep = (parts[p] * tr[f"compk_{p}"].to_numpy()).sum()
        model["k"][p] = tr[f"y_{p}"].sum() / exp_rep
    return model


def raw_parts(model, df, year_shift, Xready=None):
    X = Xready if Xready is not None else codes(align_categories(model["X"], to_pandas(df)))
    X = X.copy(); X["year"] = model["last"]
    Xs = X.drop(columns=["year"])
    out = {}
    for p in model["perils"]:
        m, base = model["freq"][p]
        lam = np.exp(base + m.predict(X, raw_score=True))
        Xs["peril"] = model["perils"].index(p)
        sev = model["sev"].predict(Xs) * np.exp(model["trend"][p] * year_shift)
        out[p] = df["exposure"].to_numpy() * lam * sev
    return out


def predict(model, df, target_year):
    parts = raw_parts(model, df, target_year - model["last"])
    return sum(parts[p] * model["k"][p] for p in model["perils"])


if __name__ == "__main__":
    import sys
    from prep import load_claims
    claims = load_claims()
    f_r, s_r = (int(a) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (300, 200)
    ys, ps = [], []
    for line in ["motor", "buildings", "contents"]:
        df = load(line).filter(pl.col("split") == "train")
        tr, va = df.filter(pl.col("year") <= 2023), df.filter(pl.col("year") == 2024)
        m = fit_line(line, tr, claims, f_r, s_r)
        p = predict(m, va, 2024) * va["completion"].to_numpy()
        y = va["y"].to_numpy()
        print(f"{line}: d2={d2(y, p):.4f} A/E={y.sum()/p.sum():.3f} trend={ {k: round(v, 3) for k, v in m['trend'].items()} } k={ {k: round(v, 2) for k, v in m['k'].items()} }", flush=True)
        ys.append(y); ps.append(p)
    Y, P = np.concatenate(ys), np.concatenate(ps)
    print(f"pooled d2={d2(Y, P):.4f}  A/E={Y.sum()/P.sum():.3f}")
