"""Guardrails for a submission file: ids, values, and level against history.

Usage:  python tools/check_sub.py outputs/baseline/submission.csv [--cleaned]

Checks (R-0501): row count equals sample_submission; row_ids unique and
identical; no nulls; predictions >= 0. Then prints, per line, the predicted
cost per exposure-year on the test rows next to the training-year burning
cost (net incurred excluding repudiated claims, raw at the valuation date,
no completion adjustment) and the maximum prediction. Read the printout —
a passing file with an implausible level is not ready (R-0208).

--cleaned uses ./outputs/cleaned/ tables for the history instead of ./data/emerging/.
Exit 0 = file checks pass; 1 = a hard check failed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
LINES = {"motor": "M", "buildings": "B", "contents": "C"}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    sub_path = Path(argv[0])
    src = ROOT / ("outputs/cleaned" if "--cleaned" in argv else "data/emerging")
    raw = ROOT / "data/emerging"

    sub = pl.read_csv(sub_path, schema_overrides={"row_id": pl.String, "prediction": pl.Float64})
    ss = pl.read_parquet(raw / "sample_submission.parquet").with_columns(pl.col("row_id").cast(pl.String))
    fails = []
    if set(sub.columns) != {"row_id", "prediction"}:
        fails.append(f"columns must be exactly row_id, prediction (got {sub.columns})")
    if sub.height != ss.height:
        fails.append(f"row count {sub.height} != sample_submission {ss.height}")
    if sub["row_id"].n_unique() != sub.height:
        fails.append("duplicate row_ids")
    if set(sub["row_id"].to_list()) != set(ss["row_id"].to_list()):
        fails.append("row_ids differ from sample_submission")
    if sub["prediction"].null_count() or not (sub["prediction"] >= 0).all():
        fails.append("null or negative predictions")
    if fails:
        print("FAIL:")
        for f in fails:
            print("  -", f)
        return 1

    # level by line: predicted on test vs history on training years
    claims = pl.read_parquet(src / "claims.parquet")
    claims = claims.filter(pl.col("status") != "repudiated").with_columns(
        (pl.col("incurred_to_date") - pl.col("recoveries")).alias("net"),
        pl.col("loss_date").cast(pl.Date).dt.year().alias("year"),
    )
    for line, prefix in LINES.items():
        te = pl.read_parquet(src / f"test_{line}.parquet").select("row_id", "exposure").with_columns(pl.col("row_id").cast(pl.String))
        te = te.join(sub, on="row_id", how="inner")
        pred_rate = te["prediction"].sum() / te["exposure"].sum()
        tr = pl.read_parquet(src / f"policies_{line}.parquet").with_columns(pl.col("period_start").cast(pl.Date).dt.year().alias("year"))
        exp = tr.group_by("year").agg(pl.col("exposure").sum().alias("exp"))
        cl = claims.filter(pl.col("line") == line).group_by("year").agg(pl.col("net").sum().alias("net"))
        hist = exp.join(cl, on="year", how="left").fill_null(0).with_columns((pl.col("net") / pl.col("exp")).round(1).alias("rate")).sort("year")
        hist_s = ", ".join(f"{y}: {r}" for y, r in zip(hist["year"], hist["rate"]))
        print(f"{line:9s} test rows {te.height:>7,d} | predicted CU per exposure-year {pred_rate:8.1f} | history (raw, at valuation) {hist_s} | max prediction {te['prediction'].max():,.0f}")
        if te.height == 0:
            print(f"  warning: no test rows matched for {line} (row_id prefix {prefix}?)")
    print("ok", sub.height, "rows — now read the levels above and explain each gap in one sentence")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
