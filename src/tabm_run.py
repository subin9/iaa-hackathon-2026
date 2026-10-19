"""TabM (k-member parameter-efficient ensemble MLP) with piecewise-linear
numeric embeddings and the Tweedie 1.5 loss, per line. Saved as "tabm".

Same inputs and offset as nn.py. Each of the k members gets its own loss;
the prediction is the mean of the members' rates.

Runs in .venv-ag:
  tabm_run.py scan     pooled D2 on both validation folds after each epoch
  tabm_run.py EPOCHS   fit all folds, save as "tabm"
"""
import sys, os
import numpy as np, polars as pl, torch
import rtdl_num_embeddings as rne
from tabm import TabM
from common import LINES, load, to_pandas, align_categories, cap_target, d2
from run import FOLDS, line_trend
import nn
from nn import encode, tweedie_loss

nn.P = float(os.environ.get("TABM_P", nn.P))  # loss power, read by tweedie_loss

MAX_EP = 8
K = 16


def train(line, last, ty, fold, epochs, seed):
    df = load(line)
    for name in filter(None, os.environ.get("TABM_FEATS", "").split(",")):
        df = df.join(pl.read_parquet(f"work/{name}_{line}.parquet"), on="row_id", how="left")
    tr = df.filter((pl.col("split") == "train") & (pl.col("year") <= last))
    te = df.filter(pl.col("split") == "test") if fold == "test" else df.filter((pl.col("split") == "train") & (pl.col("year") == ty))
    X = to_pandas(tr); Xt = align_categories(X, to_pandas(te))
    C, Ct, N, Nt, sizes = encode(X, Xt)
    keep = [j for j in range(N.shape[1]) if len(np.unique(N[:50_000, j])) > 2]  # binary missing flags stay out of the bins
    N, Nt = N[:, keep], Nt[:, keep]
    y, load_f = cap_target(tr["y"].to_numpy(), 0.99)
    w = tr["exposure"].to_numpy() * tr["completion"].to_numpy()
    base = np.log(y.sum() / w.sum())
    off = torch.tensor(np.log(w) + base, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32)
    C, Ct = torch.tensor(C, dtype=torch.long), torch.tensor(Ct, dtype=torch.long)
    N, Nt = torch.tensor(N), torch.tensor(Nt)
    torch.manual_seed(seed)
    sub = torch.randperm(len(N))[:200_000]
    bins = rne.compute_bins(N[sub], n_bins=16)
    net = TabM.make(n_num_features=N.shape[1], cat_cardinalities=sizes, d_out=1, k=K, d_block=256,
                    num_embeddings=rne.PiecewiseLinearEmbeddings(bins, 16, activation=False, version="B"))
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=3e-4)
    scale = te["exposure"].to_numpy() * load_f * np.exp(line_trend(tr) * (ty - last))
    if fold != "test":
        scale = scale * te["completion"].to_numpy()
    preds = []
    for ep in range(epochs):
        net.train()
        for idx in torch.randperm(len(yt)).split(4096):
            opt.zero_grad()
            eta = net(N[idx], C[idx]).squeeze(-1) + off[idx, None]
            tweedie_loss(eta, yt[idx, None].expand_as(eta)).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            r = torch.cat([net(Nt[i], Ct[i]).squeeze(-1).exp().mean(1) for i in torch.arange(len(Nt)).split(16384)])
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


def main(epochs, seeds=(int(os.environ.get("TABM_SEED", 0)),)):
    for fold, (last, ty) in FOLDS.items():
        parts = []
        for line in LINES:
            acc = 0
            for s in seeds:
                te, preds = train(line, last, ty, fold, epochs, s)
                acc = acc + preds[-1] / len(seeds)
            parts.append(te.select("row_id", "y", "exposure").with_columns(line=pl.lit(line), pred=pl.Series(acc)))
        out = pl.concat(parts)
        out.write_parquet(f"work/preds/{os.environ.get('TABM_NAME', 'tabm')}{seeds[0]}_{fold}.parquet")
        print("tabm", fold, "sum pred", round(out["pred"].sum()), flush=True)


if __name__ == "__main__":
    scan() if sys.argv[1] == "scan" else main(int(sys.argv[1]))
