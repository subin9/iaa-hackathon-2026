"""MLP with categorical embeddings and a Tweedie 1.5 deviance loss, per line.

The output is a log-rate added to the offset log(exposure x completion) plus
the base rate, as in the GBMs. Numerics are rank-gauss transformed with a
missing flag. Averaged over seeds and saved under the name "nn".

Runs in .venv-ag:
  nn.py scan     pooled D2 on both validation folds after each epoch
  nn.py EPOCHS   fit all folds, save as "nn"
"""
import sys, os
import numpy as np, polars as pl, pandas as pd, torch
from sklearn.preprocessing import QuantileTransformer
from common import LINES, load, to_pandas, align_categories, cap_target, d2
from run import FOLDS, line_trend

P = 1.5
MAX_EP = 12
torch.set_num_threads(int(os.environ.get("NT", 6)))


def encode(X, Xt):
    cats = [c for c in X.columns if isinstance(X[c].dtype, pd.CategoricalDtype)]
    nums = [c for c in X.columns if c not in cats and c != "year"]
    C = np.stack([X[c].cat.codes.to_numpy() + 1 for c in cats], 1)
    Ct = np.stack([Xt[c].cat.codes.to_numpy() + 1 for c in cats], 1)
    sizes = [len(X[c].cat.categories) + 1 for c in cats]
    A, At = X[nums].astype(float).to_numpy(), Xt[nums].astype(float).to_numpy()
    med = np.nanmedian(A, 0)
    miss, misst = np.isnan(A), np.isnan(At)
    A, At = np.where(miss, med, A), np.where(misst, med, At)
    qt = QuantileTransformer(output_distribution="normal", n_quantiles=200, subsample=200_000, random_state=0).fit(A)
    keep = miss.any(0)
    N = np.hstack([qt.transform(A), miss[:, keep]]).astype(np.float32)
    Nt = np.hstack([qt.transform(At), misst[:, keep]]).astype(np.float32)
    return C, Ct, N, Nt, sizes


class Net(torch.nn.Module):
    def __init__(self, sizes, n_num):
        super().__init__()
        self.emb = torch.nn.ModuleList(torch.nn.Embedding(s, min(8, (s + 1) // 2)) for s in sizes)
        d = sum(e.embedding_dim for e in self.emb) + n_num
        self.mlp = torch.nn.Sequential(torch.nn.Linear(d, 128), torch.nn.ReLU(), torch.nn.Dropout(0.1),
                                       torch.nn.Linear(128, 64), torch.nn.ReLU(), torch.nn.Linear(64, 1))
        torch.nn.init.zeros_(self.mlp[-1].weight); torch.nn.init.zeros_(self.mlp[-1].bias)

    def forward(self, c, x):
        return self.mlp(torch.cat([e(c[:, i]) for i, e in enumerate(self.emb)] + [x], 1)).squeeze(1)


def tweedie_loss(eta, y):
    return (y * torch.exp((1 - P) * eta) / (P - 1) + torch.exp((2 - P) * eta) / (2 - P)).mean()


def train(line, last, ty, fold, epochs, seed):
    df = load(line)
    tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
    te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
    X = to_pandas(tr); Xt = align_categories(X, to_pandas(te))
    C, Ct, N, Nt, sizes = encode(X, Xt)
    y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    base = np.log(y.sum() / w.sum())
    off = torch.tensor(np.log(w) + base, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32)
    C, Ct = torch.tensor(C, dtype=torch.long), torch.tensor(Ct, dtype=torch.long)
    N, Nt = torch.tensor(N), torch.tensor(Nt)
    torch.manual_seed(seed)
    net = Net(sizes, N.shape[1])
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-4)
    scale = te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
    if fold != "test":
        scale = scale * te["completion"].to_numpy()
    preds = []
    for ep in range(epochs):
        net.train()
        for idx in torch.randperm(len(yt)).split(4096):
            opt.zero_grad()
            tweedie_loss(net(C[idx], N[idx]) + off[idx], yt[idx]).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            preds.append(np.exp(net(Ct, Nt).numpy() + base) * scale)
    return te, preds


def scan():
    for fold in ("v2024", "v2023"):
        last, ty = FOLDS[fold]
        ys, ps = [], []
        for line in LINES:
            te, preds = train(line, last, ty, fold, MAX_EP, 0)
            ys.append(te["y"].to_numpy()); ps.append(preds)
        Y = np.concatenate(ys)
        print(fold, {e + 1: round(d2(Y, np.concatenate([p[e] for p in ps])), 4) for e in range(MAX_EP)}, flush=True)


def main(epochs, seeds=5):
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            acc = 0
            for s in range(seeds):
                te, preds = train(line, last, ty, fold, epochs, s)
                acc = acc + preds[-1] / seeds
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(acc)))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/nn_{fold}.parquet")
        print("nn", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    scan() if sys.argv[1] == "scan" else main(int(sys.argv[1]))
