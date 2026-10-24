"""Part 2 model: per-peril developed prior, shrunk peril levels, screened line-level corrections. One function for CV and for the final fit.

pipeline(train, score, priors): train and score are emerging rows of one line (polars, with the prior columns joined); the training rows
carry y, completion and the per-peril columns. Returns the predicted ultimate cost of each score row.
"""
import numpy as np, polars as pl
from lib import cap_target
from adapt import Adapter

SHORT = {"motor": ["gender", "new_business"], "buildings": ["policyholder_age_band"], "contents": []}   # screened, shrunk corrections per line


def peril_cols(df):
    return sorted(c[4:] for c in df.columns if c.startswith("lrp_"))


def pipeline(train, score, n0_level=400, short=None, alpha=0.1, n0_ridge=100.0, score_is_train=False, return_parts=False):
    perils = peril_cols(train); short = SHORT_DEFAULT if short is None else short
    expo_t, expo_s = train["exposure"].to_numpy(), score["exposure"].to_numpy()
    base_t = {p: np.exp(train[f"lrp_{p}"].to_numpy()) * expo_t * train[f"compk_{p}"].to_numpy() for p in perils}      # prior mean on the reported basis (cap load included)
    ult_s = {p: np.exp(score[f"lrp_{p}"].to_numpy()) * expo_s for p in perils}                                           # prior mean, ultimate basis
    comp_s = {p: (score[f"compk_{p}"].to_numpy() if score_is_train else np.ones(len(score))) for p in perils}
    ytot = sum(train[f"y_{p}"].to_numpy().sum() for p in perils); kline = ytot / sum(b.sum() for b in base_t.values())
    mult = {}
    for p in perils:
        yc, lf = cap_target(train[f"y_{p}"].to_numpy(), 0.995); kp = (yc.sum() * lf) / base_t[p].sum(); n = train[f"n_{p}"].to_numpy().sum()
        c = n / (n + n0_level); mult[p] = np.exp(np.log(kline) + c * (np.log(kp) - np.log(kline)))
    pred_t = sum(mult[p] * base_t[p] for p in perils); pred_s = sum(mult[p] * ult_s[p] * comp_s[p] for p in perils)
    info = dict(mult=mult, kline=kline)
    if short:
        ad = Adapter(short, alpha=alpha, ridge=n0_ridge).fit(train, train["y"].to_numpy(), np.log(pred_t))
        pred_s = pred_s * ad.predict(score)   # predict() carries the refitted intercept
        pred_t = pred_t * ad.predict(train); info["adapter"] = ad
    # shrinking the peril levels and the score-equation weighting of the GLM leave the training total a few percent off; put it back
    scale = ytot / pred_t.sum(); pred_s = pred_s * scale; info["scale"] = scale
    return (pred_s, info) if return_parts else pred_s


SHORT_DEFAULT = None
