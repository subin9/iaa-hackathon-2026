"""Code-graded out-of-time test for every arm (architect side).

Builds the 2024 emerging-market target from the RAW data with the minimum
treatment that involves no judgment call — claims linked to the policy row
whose period contains loss_date, net = incurred_to_date - recoveries,
repudiated claims = 0, valued at 31 Dec 2024 — and scores a holdout file
(row_id, prediction for 2024 training rows, models trained without 2024
emerging rows) with Tweedie D² (power 1.5), overall and by line.

Usage:
  python eval/grade_holdout.py <holdout_2024.csv> [--label ARM] [--append eval/holdout_results.csv]
  python eval/grade_holdout.py --naive      # 2023 burning cost x exposure, as a floor

The truth is NOT any arm's cleaned data; it is the same for every arm.
Rows missing from the file are scored as a constant (the file's own
line-level mean rate x exposure) and the coverage is reported, so a partial
file is penalised but not failed.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "week2_data" / "emerging"
LINES = ["motor", "buildings", "contents"]
POWER = 1.5


def tweedie_dev(y, mu, p=POWER):
    mu = np.maximum(mu, 1e-9)
    return 2 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))


def d2(y, mu):
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    return float(1 - tweedie_dev(y, mu).sum() / tweedie_dev(y, np.full_like(y, y.mean())).sum())


def build_truth() -> pl.DataFrame:
    claims = pl.read_parquet(RAW / "claims.parquet").with_columns(
        pl.col("loss_date").cast(pl.Date),
        pl.when(pl.col("status") == "repudiated").then(0.0)
          .otherwise(pl.col("incurred_to_date") - pl.col("recoveries")).alias("net"),
    )
    out = []
    for line in LINES:
        pol = pl.read_parquet(RAW / f"policies_{line}.parquet", columns=["row_id", "policy_id", "period_start", "period_end", "exposure"])
        pol = pol.with_columns(pl.col("row_id").cast(pl.String), pl.col("period_start").cast(pl.Date), pl.col("period_end").cast(pl.Date))
        pol = pol.with_columns(pl.col("period_start").dt.year().alias("year"))
        c = claims.filter(pl.col("line") == line).select("policy_id", "loss_date", "net")
        j = pol.join(c, on="policy_id", how="inner").filter(
            (pl.col("loss_date") >= pl.col("period_start")) & (pl.col("loss_date") <= pl.col("period_end")))
        agg = j.group_by("row_id").agg(pl.col("net").sum().alias("y"), pl.len().alias("n"))
        t = pol.join(agg, on="row_id", how="left").fill_null(0).with_columns(pl.lit(line).alias("line"))
        out.append(t.select("row_id", "line", "year", "exposure", "y", "n"))
    return pl.concat(out)


def naive_prediction(truth: pl.DataFrame) -> pl.DataFrame:
    """2023 burning cost per exposure-year by line, applied to 2024 exposure."""
    rate = truth.filter(pl.col("year") == 2023).group_by("line").agg((pl.col("y").sum() / pl.col("exposure").sum()).alias("rate"))
    t24 = truth.filter(pl.col("year") == 2024).join(rate, on="line")
    return t24.select("row_id", (pl.col("rate") * pl.col("exposure")).alias("prediction"))


def grade(pred: pl.DataFrame, truth: pl.DataFrame, label: str) -> dict:
    t24 = truth.filter(pl.col("year") == 2024)
    pred = pred.with_columns(pl.col("row_id").cast(pl.String)).unique("row_id")
    m = t24.join(pred, on="row_id", how="left")
    covered = m["prediction"].is_not_null().sum()
    extra = pred.join(t24.select("row_id"), on="row_id", how="anti").height
    # fill missing rows with the file's own line-level mean rate so a partial file is penalised, not failed
    fill = m.filter(pl.col("prediction").is_not_null()).group_by("line").agg((pl.col("prediction").sum() / pl.col("exposure").sum()).alias("fill_rate"))
    m = m.join(fill, on="line", how="left").with_columns(
        pl.when(pl.col("prediction").is_null()).then(pl.col("fill_rate") * pl.col("exposure")).otherwise(pl.col("prediction")).alias("prediction"))
    m = m.with_columns(pl.col("prediction").fill_null(0.0).clip(lower_bound=0.0))
    res = {"label": label, "graded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
           "rows_2024": t24.height, "covered": int(covered), "coverage": round(covered / t24.height, 4), "extra_rows": int(extra)}
    res["d2_all"] = round(d2(m["y"], m["prediction"]), 5)
    for line in LINES:
        s = m.filter(pl.col("line") == line)
        res[f"d2_{line}"] = round(d2(s["y"], s["prediction"]), 5)
        res[f"level_{line}"] = round(float(s["prediction"].sum() / s["y"].sum()), 4)  # predicted / actual reported
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--label", default=None)
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--append", default=None, help="CSV to append the result row to")
    a = ap.parse_args()
    if not RAW.is_dir():
        print(f"raw data not found at {RAW}"); return 1
    truth = build_truth()
    tot = truth.group_by(["line", "year"]).agg(pl.col("y").sum().round(0), pl.col("exposure").sum().round(1), pl.col("n").sum()).sort(["line", "year"])
    print("truth (reported at 31 Dec 2024, repudiated = 0):"); print(tot)
    if a.naive:
        pred, label = naive_prediction(truth), "naive_2023_rate"
    elif a.file:
        pred = pl.read_csv(a.file, schema_overrides={"row_id": pl.String, "prediction": pl.Float64})
        if set(pred.columns) != {"row_id", "prediction"}:
            print(f"columns must be row_id, prediction (got {pred.columns})"); return 1
        label = a.label or Path(a.file).parent.name
    else:
        ap.print_help(); return 1
    res = grade(pred, truth, label)
    print("\nresult:")
    for k, v in res.items():
        print(f"  {k:16s} {v}")
    print("\nlevel_* = predicted / actual reported cost (1.0 = on level; the target is reported-to-date, so an"
          " ultimate-basis prediction will read > 1 by roughly the IBNR share).")
    if a.append:
        out = Path(a.append); row = pl.DataFrame([res])
        if out.is_file():
            pl.concat([pl.read_csv(out, infer_schema_length=0), row.cast(pl.String)], how="diagonal").write_csv(out)
        else:
            row.write_csv(out)
        print(f"appended to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
