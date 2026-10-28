"""E25: weather terms with the developed-market slope on one peril. The prior leaves weather out, so the fire peril is flat in wildfire_index, although 22% of 2025
buildings rows lie above the developed maximum (0.635). Adds b * (weather - training mean) to that peril's log prior, buildings or other line CV on the cleaned files,
paired bootstrap by customer against v10's model. usage: e25_weather_peril.py LINE PERIL COLUMN B [B ...]"""
import sys; sys.path[:0] = ["part2", "src"]
import numpy as np, polars as pl
from sklearn.model_selection import GroupKFold
import model2
from e22_cleaned_round2 import prior, dev, C, BASE
from lib import LINES
ys, base_out, cs, frames = [], [], [], {}
def run(line, b, peril="fire", col="wildfire_index"):
    em = pl.read_parquet(f"{C}/{line}.parquet").filter(pl.col("split") == "train").join(prior(C, BASE, line), on="row_id").sort("row_id")
    if b: em = em.with_columns((pl.col(f"lrp_{peril}") + b * (pl.col(col).fill_null(pl.col(col).mean()) - em[col].mean())).alias(f"lrp_{peril}"))
    y = em["y"].to_numpy(); o = np.zeros(len(y))
    for tri, vai in GroupKFold(5).split(em, y, em["customer_id"].to_numpy()):
        o[vai] = model2.pipeline(em[tri], em[vai], short=model2.SHORT[line], score_is_train=True)
    return y, o, em["customer_id"].to_numpy()
# pooled denominators over all three lines, as in e21/e22
parts = {l: run(l, 0) for l in LINES}
Y = np.concatenate([parts[l][0] for l in LINES]); A = np.concatenate([parts[l][1] for l in LINES]); G = np.concatenate([parts[l][2] for l in LINES])
u, g = np.unique(G, return_inverse=True); dA = np.bincount(g, dev(Y, A)); d0 = np.bincount(g, dev(Y, np.full(len(Y), Y.mean())))
print("base pooled D2", round(1 - dA.sum() / d0.sum(), 5))
line, peril, col = sys.argv[1], sys.argv[2], sys.argv[3]
for b in [float(x) for x in sys.argv[4:]]:
    yb, ob, _ = run(line, b, peril, col)
    B = np.concatenate([ob if l == line else parts[l][1] for l in LINES])
    dB = np.bincount(g, dev(Y, B)); rng = np.random.default_rng(0)
    diff = np.array([(dA[i].sum() - dB[i].sum()) / d0[i].sum() for i in (rng.integers(0, len(u), len(u)) for _ in range(2000))])
    i = np.concatenate([np.full(len(parts[l][0]), l == line) for l in LINES])
    print(f"{line} {peril} {col} b={b:+.2f}  pooled gain {(dA.sum() - dB.sum()) / d0.sum():+.5f} sd {diff.std():.5f} P {(diff > 0).mean():.3f}  | line D2 {1 - dev(Y[i], B[i]).sum() / dev(Y[i], np.full(i.sum(), Y[i].mean())).sum():.5f} vs {1 - dev(Y[i], A[i]).sum() / dev(Y[i], np.full(i.sum(), Y[i].mean())).sum():.5f}", flush=True)
