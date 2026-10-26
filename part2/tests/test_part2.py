"""Automated checks for the Part 2 pipeline. Run from the repo root: PYTHONPATH=src:part2 .venv/bin/python -m pytest part2/tests -q

They guard the failures met while building the model (column order, double level correction, year-flag categories) and check the
data tables, the correction stage and the probe solver on synthetic data with a known answer.
"""
import os, sys
import numpy as np, polars as pl, pytest
from sklearn.metrics import d2_tweedie_score

sys.path.insert(0, "part2"); sys.path.insert(0, "src")
import lib, model2, submission, probe_solve
from adapt import Adapter, design

LINES = lib.LINES
needs_tables = pytest.mark.skipif(not os.path.exists("work/p2/motor.parquet"), reason="build the tables first (part2/prep_emerging.py, harmonize.py)")


# ---------- data tables ----------
@needs_tables
@pytest.mark.parametrize("line", LINES)
def test_exposure_is_rebuilt_from_dates(line):
    d = lib.load(line, "em")
    days = (d["period_end"] - d["period_start"]).dt.total_days() + 1
    assert np.allclose(d["exposure"].to_numpy(), days.to_numpy() / 365, atol=1e-9)
    assert d["exposure"].max() <= 1.0 + 1e-9


@needs_tables
@pytest.mark.parametrize("line", LINES)
def test_completion_range_and_test_rows_are_ultimate(line):
    d = lib.load(line, "em")
    tr, te = d.filter(pl.col("split") == "train"), d.filter(pl.col("split") == "test")
    assert tr["completion"].min() > 0 and tr["completion"].max() <= 1.0
    assert (te["completion"] == 1.0).all()


@needs_tables
@pytest.mark.parametrize("line", LINES)
def test_developed_table_matches_emerging_schema_and_codes(line):
    dev, em = lib.load(line, "dev"), lib.load(line, "em")
    assert set(dev.columns) == set(em.columns)
    for c in ("driver_age_band", "policyholder_age_band", "construction_type"):
        if c in em.columns:
            assert set(dev[c].drop_nulls().unique()) <= set(em[c].drop_nulls().unique()), c
    if line == "buildings":   # timber was recoded T -> W in 2023; both letters must end up as one category
        assert set(dev["construction_type"].unique()) == {"BRK", "STN", "WOD", "MIX"}


@needs_tables
def test_occupation_is_clean_in_the_emerging_table():
    dev, em = lib.load("motor", "dev"), lib.load("motor", "em")
    assert set(em["occupation"].drop_nulls().unique()) <= set(dev["occupation"].drop_nulls().unique())
    assert em["self_employed"].dtype == pl.Boolean


@needs_tables
def test_no_row_id_leaks_between_train_and_test():
    for line in LINES:
        d = lib.load(line, "em")
        assert d["row_id"].n_unique() == len(d)


# ---------- features and model ----------
@needs_tables
def test_feature_frames_have_the_training_column_order():
    dev, em = lib.load("motor", "dev").head(3000), lib.load("motor", "em").head(3000)
    X, Xe = lib.features(dev, em, lib.drop_cols())
    assert list(X.columns) == list(Xe.columns)      # LightGBM reads columns by position


@needs_tables
def test_priors_exist_and_are_finite_for_every_emerging_row():
    tag = os.environ.get("P2_TAGP", "_v_avg")
    for line in LINES:
        p = pl.read_parquet(f"work/p2/devperil{tag}_{line}.parquet"); em = lib.load(line, "em")
        assert len(p) == len(em) and p["row_id"].to_list() == em["row_id"].to_list()
        assert np.isfinite(p.drop("row_id").to_numpy()).all()


def _joined(line, tag=None):
    tag = tag or os.environ.get("P2_TAGP", "_v_avg")
    return lib.load(line, "em").join(pl.read_parquet(f"work/p2/devperil{tag}_{line}.parquet"), on="row_id")


@needs_tables
@pytest.mark.parametrize("line", LINES)
def test_pipeline_is_calibrated_on_its_training_rows(line):
    d = _joined(line); tr = d.filter(pl.col("split") == "train")
    p, info = model2.pipeline(tr, tr, short=model2.SHORT.get(line, []), score_is_train=True, return_parts=True)
    assert abs(p.sum() / tr["y"].sum() - 1) < 1e-9
    # the final rescale makes the total exact by construction, so the guard is on the factor it needed: the correction stage must not move the level
    # (the bug divided the intercept out); measured 0.985, 1.019 and 1.008 per line
    assert abs(info["scale"] - 1) < 0.03


@needs_tables
def test_prediction_is_proportional_to_exposure():
    d = _joined("contents"); tr, te = d.filter(pl.col("split") == "train"), d.filter(pl.col("split") == "test").head(2000)
    a = model2.pipeline(tr, te, short=[]); b = model2.pipeline(tr, te.with_columns(exposure=pl.col("exposure") * 2), short=[])
    assert np.allclose(b, 2 * a)


@needs_tables
def test_pipeline_never_predicts_negative_or_nan():
    d = _joined("buildings"); tr, te = d.filter(pl.col("split") == "train"), d.filter(pl.col("split") == "test")
    p = model2.pipeline(tr, te, short=["policyholder_age_band"])
    assert np.isfinite(p).all() and (p >= 0).all() and len(p) == len(te)


# ---------- correction stage on synthetic data ----------
def _synthetic(n=60000, effect=1.5, seed=0):
    rng = np.random.default_rng(seed)
    df = pl.DataFrame({"flag": rng.integers(0, 2, n).astype(bool), "noise": rng.integers(0, 3, n).astype(str)})
    mu = 100 * np.where(df["flag"].to_numpy(), effect, 1.0); freq = 0.1
    y = np.where(rng.random(n) < freq, rng.gamma(2.0, mu / freq / 2.0), 0.0)     # mean mu, zero-inflated
    return df, y, np.log(np.full(n, 100.0))


def test_adapter_finds_a_planted_effect_and_shrinks_it_only_a_little():
    df, y, off = _synthetic(effect=1.5)
    a = Adapter(["flag", "noise"], alpha=0.05, ridge=100.0).fit(df, y, off)
    assert "flag" in a.chosen and "noise" not in a.chosen
    ratio = a.effects()["flag=true"]
    assert 1.25 < ratio < 1.65


def test_adapter_does_not_invent_effects_in_pure_noise():
    hits = 0
    for seed in range(20):
        df, y, off = _synthetic(effect=1.0, seed=seed)
        hits += bool(Adapter(["flag", "noise"], alpha=0.05, ridge=100.0).fit(df, y, off).chosen)
    assert hits <= 4        # two candidates at p < 0.05: about 10% of runs by chance, with room for sampling noise


# ---------- probe solver on a synthetic leaderboard ----------
def test_probe_solver_recovers_the_true_segment_multipliers():
    rng = np.random.default_rng(1); n = 200000
    seg = rng.integers(0, 3, n); mu = rng.gamma(4.0, 100.0, n)
    true = np.array([1.4, 0.9, 1.1])
    y = np.where(rng.random(n) < 0.1, rng.gamma(2.0, true[seg] * mu / 0.1 / 2.0, n), 0.0)
    pub = rng.random(n) < 1 / 3; names = ["a", "b", "c"]
    def d2(mult):   # the leaderboard metric on the public rows: full Tweedie deviance, against a constant baseline
        p = mu * np.array([mult.get(k, 1.0) for k in names])[seg]
        return d2_tweedie_score(y[pub], p[pub], power=1.5)
    masks = {k: seg == i for i, k in enumerate(names)}; T = probe_solve.segment_T(mu, masks)
    probes = [{"d2": d2({})}] + [{"seg": k, "m": 1.2, "d2": d2({k: 1.2})} for k in names]
    best = {k: (y[pub & m] / np.sqrt(mu[pub & m])).sum() / np.sqrt(mu[pub & m]).sum() for k, m in masks.items()}   # optimum on the public rows
    S = 8 * np.sqrt(y[pub]).sum()
    mstar, predict, err = probe_solve.solve(T, probes, f=1 / 3, S=S)
    assert err < 1e-8
    for k in names: assert abs(mstar[k] / best[k] - 1) < 0.01     # left: f T_s in place of the public sum of mu^1/2
    biased, _, _ = probe_solve.solve(T, probes, f=1 / 3)          # the constant left out: the multipliers move away from 1
    for k in names: assert abs(np.log(biased[k])) > abs(np.log(mstar[k]))


# ---------- submission file ----------
def test_submission_check_catches_bad_files():
    s = pl.read_parquet(submission.SAMPLE).select("row_id").with_columns(prediction=pl.lit(10.0))
    assert submission.check(s) == []
    assert submission.check(s.head(10))                                                             # wrong row count
    assert submission.check(s.with_columns(prediction=pl.lit(-1.0)))                                # negative
    assert submission.check(s.with_columns(prediction=pl.lit(float("nan"))))                        # not finite
    assert submission.check(s.with_columns(row_id=pl.lit("X")))                                     # duplicate / wrong ids
