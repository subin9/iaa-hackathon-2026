"""Actuary-built model on data version D4 with the signed decisions (report/decisions_B.md).

Recipe = the harness modelling playbook as the agents applied it (R-0301/R-0302/R-0311/R-0312): one LightGBM
Tweedie(1.5) per line, 3 leaves, lr 0.02, extra_trees, 300 rounds, offset log(exposure x completion) with the
training-level intercept, capped target with the cap multiplier returned as a line factor, 3 seeds averaged.
Features: lean set minus the DROP_PART2 / DROP_RECOMMENDED lists (gender excluded per B4; weather excluded per R-0022).
Outputs (runs/hs_model/): holdout_2024.csv (2023-only -> 2024 rows, observed basis), submission_A.csv,
submission_B.csv (motor new-business x0.87), level_report.md.
Usage: python runs/hs_model/train_hs.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, polars as pl, lightgbm as lgb

ROOT = Path(__file__).resolve().parents[2]
import argparse
_ap = argparse.ArgumentParser(); _ap.add_argument("--tables", default=str(ROOT / "runs/cycle_4/modelling_tables")); _ap.add_argument("--tag", default="D4"); _ap.add_argument("--completion", default="completion")
_args = _ap.parse_args()
D = Path(_args.tables); TAG = _args.tag; COMP = _args.completion
OUT = Path(__file__).resolve().parent
LINES = ["motor", "buildings", "contents"]
SEEDS = [0, 1, 2]; ROUNDS = 300; THREADS = 2
# ---- decisions (report/decisions_B.md) ----
TREND = {"motor": 1.023, "buildings": 1.045, "contents": 1.038}          # B1-C, to mid-2025
NB_UPLIFT = {"motor": 1.00, "buildings": 1.00, "contents": 1.12}          # B3
CANDIDATE_B_MOTOR_NB = 0.87                                                # B8
IBNER = {"motor": 1.00, "buildings": 1.00, "contents": 1.00}               # B2

NON_FEATURES = {"row_id", "policy_id", "customer_id", "address_id", "split", "year", "period_start", "period_end",
                "exposure", "completion", "completion_notail", "y", "y_cap", "n_claims", "n_claims_nonrep", "n_open",
                "max_claim", "days_in_row", "start_month", "tenure_years"}
DROP_PART2 = {"x_customer_since_year", "x_campaign_code", "x_customer_service_contacts", "x_renewal_decision", "x_surname",
              "discount_applied", "gender"}
DROP_RECOMMENDED = {"make_model", "vehicle_colour", "email_domain", "marketing_consent", "document_preference",
                    "previous_insurer", "branch_id", "marketing_segment", "compulsory_excess", "written_premium",
                    "channel", "payment_method", "days_quote_to_inception", "missed_payments_12m"}
PARAMS = dict(objective="tweedie", tweedie_variance_power=1.5, num_leaves=3, learning_rate=0.02, extra_trees=True,
              feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, min_data_in_leaf=100, lambda_l2=1.0,
              cat_smooth=20, max_delta_step=0.7, num_threads=THREADS, verbose=-1)


def features(df: pl.DataFrame):
    cols = [c for c in df.columns if c not in NON_FEATURES and c not in DROP_PART2 and c not in DROP_RECOMMENDED
            and not c.startswith("dq_") and not c.startswith("wx_") and not c.startswith("x_")]
    X = df.select(cols).to_pandas()
    for c in X.columns:
        if X[c].dtype == object or str(X[c].dtype) in ("string", "str", "bool", "boolean"):
            X[c] = X[c].astype(str).astype("category")
    return X


def align(Xtr, Xte):
    for c in Xtr.columns:
        if isinstance(Xtr[c].dtype, pd.CategoricalDtype):
            Xte[c] = pd.Categorical(Xte[c].astype(str), categories=Xtr[c].cat.categories)
    return Xte


def fit_predict(tr: pl.DataFrame, te: pl.DataFrame, te_basis: np.ndarray, label: str):
    """Train on tr (y_cap, offset log(exposure*completion)), predict te on the given basis (exposure*completion*...)."""
    Xtr = features(tr); Xte = align(Xtr, features(te))
    y = tr["y_cap"].to_numpy(); e = (tr["exposure"] * tr[COMP]).to_numpy()
    intercept = np.log(y.sum() / e.sum())
    init = np.log(e) + intercept
    cap_mult = tr["y"].sum() / tr["y_cap"].sum()
    preds = []; train_level = []
    for s in SEEDS:
        ds = lgb.Dataset(Xtr, label=y, init_score=init, free_raw_data=False)
        m = lgb.train({**PARAMS, "seed": s, "bagging_seed": s, "feature_fraction_seed": s}, ds, num_boost_round=ROUNDS)
        rel_tr = np.exp(m.predict(Xtr, raw_score=True))          # relativity (model output without init score)
        p_tr = rel_tr * np.exp(init)
        train_level.append(p_tr.sum() / y.sum())
        rel_te = np.exp(m.predict(Xte, raw_score=True))
        preds.append(rel_te * np.exp(intercept) * te_basis)
    p = np.mean(preds, axis=0); lvl = float(np.mean(train_level))
    # R-0311 gate: training total must reconcile; apply explicit factor if not
    factor = 1.0 if abs(lvl - 1) < 0.03 else 1.0 / lvl
    return p * cap_mult * factor, dict(label=label, cap_mult=round(cap_mult, 4), train_level=round(lvl, 4),
                                       explicit_factor=round(factor, 4), n_features=Xtr.shape[1])


def main():
    report = []; hold = []; subA = []; subB = []
    for ln in LINES:
        df = pl.read_parquet(D / f"{ln}.parquet")
        tr = df.filter(pl.col("split") == "train"); te = df.filter(pl.col("split") == "test")
        # holdout: 2023 -> 2024 on the observed basis
        tr23 = tr.filter(pl.col("year") == 2023); tr24 = tr.filter(pl.col("year") == 2024)
        basis24 = (tr24["exposure"] * tr24[COMP]).to_numpy()
        p24, info = fit_predict(tr23, tr24, basis24, f"{ln} holdout 2023->2024")
        hold.append(pl.DataFrame({"row_id": tr24["row_id"], "prediction": p24}))
        report.append(info)
        # submission: 2023+2024 -> 2025 ultimate (completion = 1)
        basis25 = te["exposure"].to_numpy()
        p25, info2 = fit_predict(tr, te, basis25, f"{ln} final 2023+2024->2025")
        nb = te["new_business"].cast(pl.Boolean).to_numpy()
        pA = p25 * TREND[ln] * IBNER[ln] * np.where(nb, NB_UPLIFT[ln], 1.0)
        pB = pA * (np.where(nb, CANDIDATE_B_MOTOR_NB, 1.0) if ln == "motor" else 1.0)
        subA.append(pl.DataFrame({"row_id": te["row_id"], "prediction": pA})); subB.append(pl.DataFrame({"row_id": te["row_id"], "prediction": pB}))
        info2.update(level_2025_A=round(float(pA.sum() / te["exposure"].sum()), 1), level_2025_B=round(float(pB.sum() / te["exposure"].sum()), 1),
                     nb_share_rows=round(float(nb.mean()), 3))
        report.append(info2)
        print(info, "\n", info2)
    sfx = "" if TAG == "D4" else f"_{TAG}"
    pl.concat(hold).write_csv(OUT / f"holdout_2024{sfx}.csv"); pl.concat(subA).write_csv(OUT / f"submission_A{sfx}.csv"); pl.concat(subB).write_csv(OUT / f"submission_B{sfx}.csv")
    (OUT / f"level_report{sfx}.json").write_text(json.dumps(report, indent=2))
    print(f"written: holdout_2024{sfx}.csv, submission_A{sfx}.csv, submission_B{sfx}.csv")


if __name__ == "__main__":
    sys.exit(main())
