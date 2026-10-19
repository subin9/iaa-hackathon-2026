"""Experiment harness over both validation folds (train <= 2023 score 2024, train <= 2022 score 2023).

Each config is a JSON object:
  params   LightGBM overrides on exp.BASE (objective defaults to Tweedie 1.5)
  cap      target cap quantile (default 0.99)
  feats    true to join work/feats_{line}.parquet, or a list of file prefixes
  drop     extra columns to drop
  seeds    number of seeds to average (default 1)
  decay    per-year weight multiplier for older years (1 = flat)
  premium_offset  true: offset log(written premium x completion) instead of exposure
  pooled   true: one model over all three lines with line as a feature
  dglm     exponent g: a first fit gives Tweedie unit deviances, a gamma GBM
           models them as dispersion phi(x), and the final fit uses weight phi^-g
           (double GLM idea of Smyth and Jorgensen, 2002)
  te       [columns, K]: add log credibility-weighted cost rate per level,
           out-of-fold by policy for training rows (Buhlmann-Straub, weight K)
  distill  a in (0, 1): train on a*y + (1-a)*teacher, where the teacher is a
           5-fold out-of-fold fit of the same model grouped by policy
Prints pooled D2 per fold at each round count, and the mean of the two folds.

usage: exp2.py CONFIG_JSONL
"""
import sys, os, json, time
import numpy as np, polars as pl, lightgbm as lgb
from common import LINES, load, to_pandas, align_categories, d2, cap_target
from exp import BASE, codes

ROUNDS = (100, 150, 200, 300, 400)
FOLDS = ((2023, 2024), (2022, 2023))


def table(line, cfg):
    df = load(line).filter(pl.col("split") == "train")
    feats = cfg.get("feats", [])
    for name in (["feats"] if feats is True else feats):
        df = df.join(pl.read_parquet(f"work/{name}_{line}.parquet"), on="row_id", how="left")
    return df


def distill(P, X, y, w, base, sw, groups, a, rounds):
    fold_of = np.array([hash(g) % 5 for g in groups])
    oof = np.zeros_like(y)
    for k in range(5):
        t, v = fold_of != k, fold_of == k
        m = lgb.train(P, lgb.Dataset(X[t], y[t], weight=sw[t], init_score=np.log(w[t]) + base), rounds)
        oof[v] = np.exp(base + m.predict(X[v], raw_score=True)) * w[v]
    return a * y + (1 - a) * oof


def dispersion_weight(P, X, y, w, base, sw, g, rounds):
    p = P.get("tweedie_variance_power", 1.5)
    m = lgb.train(P, lgb.Dataset(X, y, weight=sw, init_score=np.log(w) + base), rounds)
    mu = np.exp(base + m.predict(X, raw_score=True)) * w
    dev = 2 * (np.maximum(y, 0) ** (2 - p) / ((1 - p) * (2 - p)) - y * mu ** (1 - p) / (1 - p) + mu ** (2 - p) / (2 - p))
    dev = dev / mu ** (2 - p) * w ** (1 - p)  # unit deviance scaled so that E[dev] is about phi / w^(p-1) free of mu
    Q = {"objective": "gamma", "learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 2000,
         "num_threads": P["num_threads"], "verbose": -1}
    phi = lgb.train(Q, lgb.Dataset(X, dev + 1e-6, weight=sw), 100).predict(X)
    wt = (phi / phi.mean()) ** -g
    return np.clip(wt / wt.mean(), 0.2, 5)


def cred_encode(lv, lv_val, y, w, groups, K):
    prior = y.sum() / w.sum()

    def table(m):
        d = pl.DataFrame({"l": lv[m], "y": y[m], "w": w[m]}).group_by("l").agg(pl.col("y").sum(), pl.col("w").sum())
        return dict(zip(d["l"], np.log((d["y"] + K * prior) / (d["w"] + K))))
    tr_enc = np.empty(len(lv))
    for k in range(5):
        t = table(groups != k)
        tr_enc[groups == k] = [t.get(v, np.log(prior)) for v in lv[groups == k]]
    t = table(np.ones(len(lv), bool))
    return tr_enc, np.array([t.get(v, np.log(prior)) for v in lv_val])


def fold(cfg, last, vy, tables):
    ROUNDS = tuple(cfg.get("rounds", globals()["ROUNDS"]))
    P = {**BASE, "num_threads": int(os.environ.get("NT", 6)), **cfg.get("params", {})}
    ys, ps = [], {r: [] for r in ROUNDS}
    for line, df in tables.items():
        tr, va = df.filter(pl.col("year") <= last), df.filter(pl.col("year") == vy)
        drop = cfg.get("drop", [])
        X = codes(to_pandas(tr, drop)); Xv = codes(align_categories(to_pandas(tr, drop), to_pandas(va, drop)))
        Xv["year"] = last
        w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
        wv = va["exposure"].to_numpy() * va["completion"].to_numpy()
        if line == "all":  # pooled lines: cap, load and base level stay per line
            lt, lv = tr["line"].to_numpy(), va["line"].to_numpy()
            y, load_f = tr["y"].to_numpy().astype(float), np.ones(len(va))
            base, base_v = np.zeros(len(tr)), np.zeros(len(va))
            for l in LINES:
                y[lt == l], load_f[lv == l] = cap_target(y[lt == l], cfg.get("cap", 0.99))
                base[lt == l] = base_v[lv == l] = np.log(y[lt == l].sum() / w[lt == l].sum())
        else:
            y, load_f = cap_target(tr["y"].to_numpy(), cfg.get("cap", 0.99))
        if cfg.get("premium_offset"):  # model the loss ratio on the insurer's own price
            w = w * tr["premium_rate"].to_numpy()
            wv = wv * va["premium_rate"].to_numpy()
        if line != "all":
            base = base_v = np.log(y.sum() / w.sum())
        sw = cfg.get("decay", 1.0) ** (last - tr["year"].to_numpy())
        if "distill" in cfg:
            y = distill(P, X, y, w, base, sw, tr["policy_id"].to_numpy(), cfg["distill"], cfg.get("teacher_rounds", 150))
        if "te" in cfg:
            cols, K = cfg["te"]
            groups = np.array([hash(g) % 5 for g in tr["policy_id"].to_numpy()])
            for c in (c for c in cols if c in tr.columns):
                X[f"te_{c}"], Xv[f"te_{c}"] = cred_encode(tr[c].cast(pl.Utf8).to_numpy(), va[c].cast(pl.Utf8).to_numpy(), y, w, groups, K)
        if "dglm" in cfg:
            sw = sw * dispersion_weight(P, X, y, w, base, sw, cfg["dglm"], cfg.get("dglm_rounds", 200))
        acc = {r: 0 for r in ROUNDS}
        for s in range(cfg.get("seeds", 1)):
            m = lgb.train({**P, "seed": cfg.get("seed0", 0) + s}, lgb.Dataset(X, y, weight=sw, init_score=np.log(w) + base), max(ROUNDS))
            for r in ROUNDS:
                acc[r] = acc[r] + np.exp(base_v + m.predict(Xv, raw_score=True, num_iteration=r))
        ys.append(va["y"].to_numpy())
        for r in ROUNDS:
            ps[r].append(acc[r] / cfg.get("seeds", 1) * wv * load_f)
    Y = np.concatenate(ys)
    out = {}
    for r in ROUNDS:
        p = np.concatenate(ps[r])
        out[r] = (d2(Y, p), d2(Y, p * Y.sum() / p.sum()))  # raw and level-matched
    return out


if __name__ == "__main__":
    for line_cfg in open(sys.argv[1]):
        if not line_cfg.strip() or line_cfg.startswith("#"):
            continue
        cfg = json.loads(line_cfg); t = time.time()
        tables = {l: table(l, cfg) for l in LINES}
        if cfg.get("pooled"):
            tables = {"all": pl.concat([t.with_columns(line=pl.lit(l)) for l, t in tables.items()], how="diagonal_relaxed")}
        res = [fold(cfg, last, vy, tables) for last, vy in FOLDS]
        R = tuple(cfg.get("rounds", ROUNDS))
        mean = {r: (res[0][r][1] + res[1][r][1]) / 2 for r in R}
        best = max(mean, key=mean.get)
        print(json.dumps(cfg), f"| best r {best} mean(level-matched) {mean[best]:.4f}",
              f"v2024 {res[0][best][0]:.4f}/{res[0][best][1]:.4f} v2023 {res[1][best][0]:.4f}/{res[1][best][1]:.4f}",
              f"| {time.time() - t:.0f}s", flush=True)
        print("   ", {r: round(mean[r], 4) for r in R}, flush=True)
