"""Write the equal-weight blend submission with the policy credibility factor.

The base models get weight 1, the TabM seed average weight 3, and each extra
group weight 3 after its line totals are matched to the TabM average. The
policy factor (12 + N) / (12 + L) is renormalised per line, then the whole
submission is scaled.

usage: make_sub.py OUT SCALE [GROUP ...]   GROUP is a comma-separated list of prediction names
"""
import sys
import numpy as np, polars as pl
from blend import frame

BASE = "tw po fs ag twx pox fs5 glm cb nn ebm".split()


def per_line(ln, num, den):
    out = num.copy()
    for l in np.unique(ln):
        i = ln == l; out[i] *= den[i].sum() / num[i].sum()
    return out


def blend(fold, groups):
    df = frame(BASE + ["tmavg6"] + [m for g in groups for m in g], fold)
    ln, ref = df["line"].to_numpy(), df["tmavg6"].to_numpy()
    b = sum(df[c].to_numpy() for c in BASE) + 3 * ref
    for g in groups:
        b = b + 3 * per_line(ln, sum(df[m].to_numpy() for m in g) / len(g), ref)
    b = b / (len(BASE) + 3 + 3 * len(groups))
    e = df.select("row_id").join(pl.read_parquet(f"work/exprateoof_{fold}.parquet").select("row_id", "N_policy_id", "L_policy_id"), on="row_id", how="left")
    m = ((12 + e["N_policy_id"].fill_null(0).cast(pl.Float64)) / (12 + e["L_policy_id"].fill_null(0))).to_numpy()
    return df, per_line(ln, b * m, b)


if __name__ == "__main__":
    out, scale, groups = sys.argv[1], float(sys.argv[2]), [g.split(",") for g in sys.argv[3:]]
    df, p = blend("test", groups)
    pl.DataFrame({"row_id": df["row_id"], "prediction": p * scale}).write_csv(out)
