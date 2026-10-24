"""Fit the Part 2 pipeline on all emerging training rows and score the 2025 test rows.
usage: fit_final.py OUT.csv [--tag _v_avg] [--n0 400]   (the correction specs are model2.SHORT)
Also writes OUT.parquet with row_id, line, new_business and the prediction, for the probe and diagnostics scripts."""
import sys, argparse; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import *
import model2, submission
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--tag", default="_v_avg"); ap.add_argument("--n0", type=float, default=400.0)
a = ap.parse_args()
short = model2.SHORT
parts = []
for line in LINES:
    em = load(line, "em").join(pl.read_parquet(f"work/p2/devperil{a.tag}_{line}.parquet"), on="row_id")
    tr, te = em.filter(pl.col("split") == "train"), em.filter(pl.col("split") == "test")
    p, info = model2.pipeline(tr, te, n0_level=a.n0, short=short[line], return_parts=True)
    print(line, "k_line", round(float(info["kline"]), 3), "peril multipliers", {k: round(float(v), 2) for k, v in info["mult"].items()}, "| mean rate/exposure yr", round(float(p.sum() / te["exposure"].sum()), 1),
          "| corrections:", [(sp["cols"], sp.get("perils"), ad.effects()) for sp, ad in info["adapters"]])
    parts.append(pl.DataFrame({"row_id": te["row_id"], "prediction": p, "line": line, "new_business": te["new_business"]}))
allp = pl.concat(parts); allp.write_parquet(a.out.replace(".csv", ".parquet")); submission.write(allp.select("row_id", "prediction"), a.out)
