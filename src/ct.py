"""Credibility Transformer (Richman, Scognamiglio and Wuthrich, 2024) with the
Tweedie 1.5 loss, per line. Saved as "ct".

Every covariate becomes a token (entity embedding for categoricals, piecewise
linear embedding for numerics) plus a learned position vector, and a CLS token
is appended. On a random share 1 - ALPHA of training steps the CLS token may
only attend to itself, so it learns a covariate-free prior that the
covariate-informed CLS is shrunk towards. Inference always uses full attention.

Runs in .venv-ag:
  ct.py scan     pooled D2 on both validation folds after each epoch
  ct.py EPOCHS   fit all folds, save as "ct{CT_SEED}"
"""
import sys, os
import numpy as np, polars as pl, torch
import rtdl_num_embeddings as rne
from common import LINES, load, to_pandas, align_categories, cap_target, d2
from run import FOLDS, line_trend
from nn import encode, tweedie_loss

MAX_EP = 6
D, HEADS, LAYERS = 32, 2, 2
ALPHA = float(os.environ.get("CT_ALPHA", 0.95))
torch.set_num_threads(int(os.environ.get("NT", 6)))


class CT(torch.nn.Module):
    def __init__(self, sizes, bins):
        super().__init__()
        self.emb = torch.nn.ModuleList(torch.nn.Embedding(s, D) for s in sizes)
        self.num = rne.PiecewiseLinearEmbeddings(bins, D, activation=True, version="B")
        t = len(sizes) + len(bins)
        self.pos = torch.nn.Parameter(torch.randn(t + 1, D) * 0.02)
        self.cls = torch.nn.Parameter(torch.randn(1, 1, D) * 0.02)
        layer = torch.nn.TransformerEncoderLayer(D, HEADS, 2 * D, dropout=0.05, activation="gelu", batch_first=True, norm_first=True)
        self.enc = torch.nn.TransformerEncoder(layer, LAYERS, enable_nested_tensor=False)
        self.head = torch.nn.Sequential(torch.nn.LayerNorm(D), torch.nn.Linear(D, 16), torch.nn.GELU(), torch.nn.Linear(16, 1))
        torch.nn.init.zeros_(self.head[-1].weight); torch.nn.init.zeros_(self.head[-1].bias)
        prior = torch.zeros(t + 1, t + 1, dtype=torch.bool)
        prior[t, :t] = True  # CLS sees only itself
        self.register_buffer("prior_mask", prior)

    def forward(self, x, c, prior=False):
        tok = torch.cat([torch.stack([e(c[:, i]) for i, e in enumerate(self.emb)], 1), self.num(x),
                         self.cls.expand(len(x), -1, -1)], 1) + self.pos
        h = self.enc(tok, mask=self.prior_mask if prior else None)
        return self.head(h[:, -1]).squeeze(-1)


def train(line, last, ty, fold, epochs, seed):
    df = load(line)
    tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
    te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
    X = to_pandas(tr); Xt = align_categories(X, to_pandas(te))
    C, Ct, N, Nt, sizes = encode(X, Xt)
    keep = [j for j in range(N.shape[1]) if len(np.unique(N[:50_000, j])) > 2]
    N, Nt = N[:, keep], Nt[:, keep]
    y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    base = np.log(y.sum() / w.sum())
    off = torch.tensor(np.log(w) + base, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32)
    C, Ct = torch.tensor(C, dtype=torch.long), torch.tensor(Ct, dtype=torch.long)
    N, Nt = torch.tensor(N), torch.tensor(Nt)
    torch.manual_seed(seed)
    bins = rne.compute_bins(N[torch.randperm(len(N))[:200_000]], n_bins=16)
    net = CT(sizes, bins)
    opt = torch.optim.AdamW(net.parameters(), lr=float(os.environ.get("CT_LR", 1e-3)), weight_decay=0.02, betas=(0.9, 0.95))
    scale = te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
    if fold != "test":
        scale = scale * te["completion"].to_numpy()
    preds = []
    for ep in range(epochs):
        net.train()
        for idx in torch.randperm(len(yt)).split(4096):
            opt.zero_grad()
            eta = net(N[idx], C[idx], prior=bool(torch.rand(()) > ALPHA)) + off[idx]
            tweedie_loss(eta, yt[idx]).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            r = torch.cat([net(Nt[i], Ct[i]).exp() for i in torch.arange(len(Nt)).split(16384)])
        preds.append(r.numpy() * np.exp(base) * scale)
    return te, preds


def scan():
    for fold in ("v2024", "v2023"):
        last, ty = FOLDS[fold]
        ys, ps = [], []
        for line in LINES:
            te, preds = train(line, last, ty, fold, MAX_EP, 0)
            ys.append(te["y"].to_numpy()); ps.append(preds)
            print(fold, line, "done", flush=True)
        Y = np.concatenate(ys)
        print(fold, {e + 1: round(d2(Y, np.concatenate([p[e] for p in ps])), 4) for e in range(MAX_EP)}, flush=True)


def main(epochs, seed=int(os.environ.get("CT_SEED", 0))):
    for fold, (last, ty) in FOLDS.items():
        parts, ys, ps = [], [], []
        for line in LINES:
            te, preds = train(line, last, ty, fold, epochs, seed)
            ys.append(te["y"].to_numpy()); ps.append(preds)
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(preds[-1])))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/ct{seed}_{fold}.parquet")
        if fold != "test":
            Y = np.concatenate(ys)
            print(fold, {e + 1: round(d2(Y, np.concatenate([p[e] for p in ps])), 4) for e in range(epochs)}, flush=True)
        print("ct", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    scan() if sys.argv[1] == "scan" else main(int(sys.argv[1]))
