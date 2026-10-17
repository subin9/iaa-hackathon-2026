"""Train 2024 vs test 2025: which features tell them apart?"""
import sys; sys.path.insert(0, "src")
import numpy as np, polars as pl, lightgbm as lgb
from sklearn.metrics import roc_auc_score
from common import LINES, load, to_pandas, align_categories
from exp import codes
for line in LINES:
    df = load(line)
    a = df.filter((pl.col("split") == "train") & (pl.col("year") == 2024)); b = df.filter(pl.col("split") == "test")
    X = codes(to_pandas(pl.concat([a, b]), ["year"]))
    lab = np.r_[np.zeros(a.height), np.ones(b.height)]
    idx = np.random.default_rng(0).permutation(len(lab)); tr, va = idx[: len(idx) // 2], idx[len(idx) // 2:]
    m = lgb.train(dict(objective="binary", learning_rate=0.1, num_leaves=31, verbose=-1, num_threads=8), lgb.Dataset(X.iloc[tr], lab[tr]), 200)
    auc = roc_auc_score(lab[va], m.predict(X.iloc[va]))
    imp = m.feature_importance("gain"); top = np.argsort(-imp)[:6]
    print(line, "AUC", round(auc, 4), [(m.feature_name()[i], round(imp[i] / imp.sum(), 3)) for i in top], flush=True)
