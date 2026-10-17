"""AutoGluon on the same folds as run.py, saved under the name "ag".

AutoGluon has no offset, so it models the rate y / (exposure x completion)
with sample weight (exposure x completion)^(2 - 1.5). For a Tweedie loss with
power 1.5 and a log link this is the same fit as the offset form. Its models
use Tweedie losses and a weighted Tweedie deviance as the stopping metric.

Runs in .venv-ag: .venv-ag/bin/python src/ag.py [time_limit_seconds]
"""
import sys, os
import numpy as np, polars as pl
from sklearn.metrics import mean_tweedie_deviance
from autogluon.core.metrics import make_scorer
from autogluon.tabular import TabularPredictor
from common import LINES, load, to_pandas, align_categories, cap_target
from run import FOLDS, line_trend

P = 1.5
tweedie = make_scorer("tweedie15", lambda y, p, sample_weight=None: mean_tweedie_deviance(
    y, np.maximum(p, 1e-9), sample_weight=sample_weight, power=P), optimum=0, greater_is_better=False)
HP = {
    "GBM": [{"objective": "tweedie", "tweedie_variance_power": P, "learning_rate": 0.03, "num_leaves": 15, "min_data_in_leaf": 2000, "ag_args": {"name_suffix": "Tw"}}],
    "CAT": [{"loss_function": f"Tweedie:variance_power={P}", "learning_rate": 0.05, "depth": 6, "ag_args": {"name_suffix": "Tw"}}],
    "XGB": [{"objective": "reg:tweedie", "tweedie_variance_power": P, "learning_rate": 0.05, "max_depth": 4, "min_child_weight": 50, "ag_args": {"name_suffix": "Tw"}}],
}


def main(time_limit):
    os.makedirs("work/preds", exist_ok=True)
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            df = load(line)
            tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
            te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
            X = to_pandas(tr); Xt = align_categories(X, to_pandas(te))
            y, load_f = cap_target(tr["y"].to_numpy(), 0.995)
            w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
            X["rate"] = y / w
            X["w"] = w ** (2 - P)
            pr = TabularPredictor(label="rate", sample_weight="w", weight_evaluation=True, eval_metric=tweedie,
                                  problem_type="regression", path=f"AutogluonModels/{fold}_{line}", verbosity=1)
            pr.fit(X, hyperparameters=HP, time_limit=time_limit, presets="good_quality", num_cpus=16)
            print(pr.leaderboard(silent=True)[["model", "score_val"]].to_string(), flush=True)
            Xt["year"] = int(tr["year"].max())
            rate = np.maximum(pr.predict(Xt).to_numpy(), 0)
            p = rate * te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
            if fold != "test":
                p = p * te["completion"].to_numpy()
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(p)))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/ag_{fold}.parquet")
        print("ag", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 900)
