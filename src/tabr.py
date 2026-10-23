"""Retrieval network with the Tweedie 1.5 loss, per line (ModernNCA-style, GPU).

A row is embedded by an MLP. Its rate is a credibility-weighted average of the rates of
candidate training rows, with kernel weight exp(-squared distance) in the embedding:
  rate = (sum_j k_ij y_j + kappa rate0) / (sum_j k_ij w_j + kappa)
plus a small zero-initialised MLP correction. Training draws a random candidate set per
step; inference averages over several random candidate sets of the same size. The
prediction is exposure x completion x rate, trended like the other models.

usage: tabr.py FOLD[,FOLD..] EPOCHS NAME   (FOLD in v2024 v2023 test; scores print per epoch)
"""
import sys, os
import numpy as np, polars as pl, pandas as pd, torch
from sklearn.preprocessing import QuantileTransformer
from common import LINES, load, to_pandas, align_categories, cap_target, d2, LEAN

FOLDS = {"v2024": (2023, 2024), "v2023": (2022, 2023), "test": (2024, 2025)}
P = 1.5
NC = int(os.environ.get("TR_NC", 8192))
D = int(os.environ.get("TR_D", 128))
dev = "cuda"


def line_trend(tr):
    g = tr.group_by("year").agg(
        c=(pl.col("completion") * pl.col("exposure")).sum() / pl.col("exposure").sum(),
        r=pl.col("y").sum() / (pl.col("exposure") * pl.col("completion")).sum()).filter(pl.col("c") > 0.97).sort("year")
    return np.polyfit(g["year"].to_numpy(), np.log(g["r"].to_numpy()), 1)[0]


def encode(X, Xt):
    cats = [c for c in X.columns if isinstance(X[c].dtype, pd.CategoricalDtype)]
    nums = [c for c in X.columns if c not in cats]
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
        self.enc = torch.nn.Sequential(torch.nn.Linear(d, 256), torch.nn.ReLU(), torch.nn.Dropout(float(os.environ.get("TR_DO", 0.0))), torch.nn.Linear(256, D))
        self.head = torch.nn.Sequential(torch.nn.Linear(D, 64), torch.nn.ReLU(), torch.nn.Linear(64, 1))
        torch.nn.init.zeros_(self.head[-1].weight); torch.nn.init.zeros_(self.head[-1].bias)
        self.log_kappa = torch.nn.Parameter(torch.tensor(1.0))

    def embed(self, c, x):
        return self.enc(torch.cat([e(c[:, i]) for i, e in enumerate(self.emb)] + [x], 1))

    def forward(self, c, x, cand, rate0):
        """cand = (embedding, y, w) of the candidate rows; returns the log rate."""
        q = self.embed(c, x)
        ce, cy, cw = cand
        k = torch.exp(-torch.cdist(q, ce).pow(2) / D)
        rate = (k @ cy + self.log_kappa.exp() * rate0) / (k @ cw + self.log_kappa.exp())
        return torch.log(rate) + self.head(q).squeeze(1)


def loss_fn(eta, y):
    return (y * torch.exp((1 - P) * eta) / (P - 1) + torch.exp((2 - P) * eta) / (2 - P)).mean()


def train(line, last, ty, fold, epochs, seed):
    df = load(line)
    tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
    te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
    drop = LEAN + ["year"]
    X = to_pandas(tr, drop); Xt = align_categories(X, to_pandas(te, drop))
    C, Ct, N, Nt, sizes = encode(X, Xt)
    y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    rate0 = float(y.sum() / w.sum())
    T = lambda a, dt=torch.float32: torch.tensor(a, dtype=dt, device=dev)
    C, Ct, N, Nt, yt, wt = T(C, torch.long), T(Ct, torch.long), T(N), T(Nt), T(y), T(w)
    torch.manual_seed(seed)
    net = Net(sizes, N.shape[1]).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=float(os.environ.get("TR_WD", 1e-4)))
    scale = te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
    if fold != "test":
        scale = scale * te["completion"].to_numpy()
    n = len(yt); preds = []
    steps = epochs * ((n + 1023) // 1024)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=float(os.environ.get("TR_LR", 1e-3)), total_steps=steps, pct_start=0.1)
    for ep in range(epochs):
        net.train()
        for idx in torch.randperm(n, device=dev).split(1024):
            cj = torch.randint(0, n, (NC,), device=dev)
            ce = net.embed(C[cj], N[cj])
            eta = net(C[idx], N[idx], (ce, yt[cj], wt[cj]), rate0) + torch.log(wt[idx])
            opt.zero_grad(); loss_fn(eta, yt[idx]).backward(); opt.step(); sched.step()
        net.eval()
        with torch.no_grad():
            out = torch.zeros(len(Nt), device=dev)
            for _ in range(8):
                cj = torch.randint(0, n, (NC,), device=dev)
                cand = (net.embed(C[cj], N[cj]), yt[cj], wt[cj])
                out += torch.cat([net(Ct[i], Nt[i], cand, rate0).exp() for i in torch.arange(len(Nt), device=dev).split(4096)]) / 8
        preds.append(out.cpu().numpy() * scale)
    return te, preds


def main(folds, epochs, name):
    os.makedirs("preds", exist_ok=True)
    for fold in folds:
        last, ty = FOLDS[fold]
        parts, per_ep = [], []
        for line in LINES:
            te, preds = train(line, last, ty, fold, epochs, int(os.environ.get("TR_SEED", 0)))
            per_ep.append((te["y"].to_numpy(), preds))
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(preds[-1])))
            print(fold, line, "done", flush=True)
        if fold != "test":
            Y = np.concatenate([a for a, _ in per_ep])
            for e in range(epochs):
                q = np.concatenate([p[e] for _, p in per_ep])
                print(fold, "epoch", e + 1, round(d2(Y, q), 4), "level-matched", round(d2(Y, q * Y.sum() / q.sum()), 4), flush=True)
        pl.concat(parts).write_parquet(f"preds/{name}_{fold}.parquet")


if __name__ == "__main__":
    main(sys.argv[1].split(","), int(sys.argv[2]), sys.argv[3])
