"""Part 2 model: per-peril developed prior, shrunk peril levels, screened corrections. One function for CV and for the final fit.

pipeline(train, score): train and score are emerging rows of one line (polars, with the per-peril prior columns lrp_* joined); the training rows
carry y, the per-peril y_*, n_* and compk_* columns. Returns the predicted ultimate cost of each score row (reported cost if score_is_train).
A correction spec is {"cols": [...], "perils": [...] or None}: the screened factors are fitted on the cost of those perils only and scale
only those perils' predictions. A plain list of column names means one spec over all perils.
"""
import numpy as np, polars as pl
from lib import cap_target
from adapt import Adapter

COLLISION = ["bodily_injury", "own_damage", "third_party_prop"]
# gender moves the at-fault perils (male/female frequency ratio 1.66, 1.30, 1.43) and not glass or theft (1.04, 1.17), see LOG.md
SHORT = {"motor": [{"cols": ["gender"], "perils": COLLISION}], "buildings": [{"cols": ["policyholder_age_band"]}], "contents": []}


def peril_cols(df):
    return sorted(c[4:] for c in df.columns if c.startswith("lrp_"))


def _specs(short):
    if not short: return []
    if isinstance(short[0], str): return [{"cols": list(short), "perils": None}]
    return list(short)


def pipeline(train, score, n0_level=400, short=None, alpha=0.1, n0_ridge=100.0, score_is_train=False, return_parts=False):
    perils = peril_cols(train); specs = _specs(short)
    expo_t, expo_s = train["exposure"].to_numpy(), score["exposure"].to_numpy()
    base_t = {p: np.exp(train[f"lrp_{p}"].to_numpy()) * expo_t * train[f"compk_{p}"].to_numpy() for p in perils}      # prior mean on the reported basis (cap load included)
    ult_s = {p: np.exp(score[f"lrp_{p}"].to_numpy()) * expo_s for p in perils}                                           # prior mean, ultimate basis
    comp_s = {p: (score[f"compk_{p}"].to_numpy() if score_is_train else np.ones(len(score))) for p in perils}
    ytot = sum(train[f"y_{p}"].to_numpy().sum() for p in perils); kline = ytot / sum(b.sum() for b in base_t.values())
    mult = {}
    for p in perils:
        yc, lf = cap_target(train[f"y_{p}"].to_numpy(), 0.995); kp = (yc.sum() * lf) / base_t[p].sum(); n = train[f"n_{p}"].to_numpy().sum()
        c = n / (n + n0_level); mult[p] = np.exp(np.log(kline) + c * (np.log(kp) - np.log(kline)))
    part_t = {p: mult[p] * base_t[p] for p in perils}; part_s = {p: mult[p] * ult_s[p] * comp_s[p] for p in perils}
    info = dict(mult=mult, kline=kline, adapters=[])
    for spec in specs:
        grp = spec.get("perils") or perils
        gt = sum(part_t[p] for p in grp); yg = sum(train[f"y_{p}"].to_numpy() for p in grp)
        ad = Adapter(spec["cols"], alpha=alpha, ridge=n0_ridge).fit(train, yg, np.log(gt))
        ft, fs = ad.predict(train), ad.predict(score)       # predict() carries the refitted intercept
        for p in grp: part_t[p] = part_t[p] * ft; part_s[p] = part_s[p] * fs
        info["adapters"].append((spec, ad))
    pred_t, pred_s = sum(part_t.values()), sum(part_s.values())
    # shrinking the peril levels and the score-equation weighting of the GLM leave the training total a few percent off; put it back
    scale = ytot / pred_t.sum(); info["scale"] = scale
    pred_s = pred_s * scale
    return (pred_s, info) if return_parts else pred_s
