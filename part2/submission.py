"""Write and check a Part 2 submission file (row_id, prediction) against the emerging-market sample submission."""
import sys
import numpy as np, polars as pl

SAMPLE = "data/part2/emerging/sample_submission.parquet"


def check(df: pl.DataFrame) -> list[str]:
    """Return a list of problems; an empty list means the file passes."""
    s = pl.read_parquet(SAMPLE); bad = []
    if df.columns != ["row_id", "prediction"]: bad.append(f"columns are {df.columns}")
    if len(df) != len(s): bad.append(f"{len(df)} rows, expected {len(s)}")
    if df["row_id"].n_unique() != len(df): bad.append("row_id not unique")
    if set(df["row_id"].to_list()) != set(s["row_id"].to_list()): bad.append("row_id set differs from the sample submission")
    p = df["prediction"].to_numpy()
    if not np.isfinite(p).all(): bad.append("non-finite predictions")
    if (p < 0).any(): bad.append("negative predictions")
    return bad


def write(df: pl.DataFrame, path: str):
    bad = check(df)
    if bad: raise SystemExit("submission check failed: " + "; ".join(bad))
    df.write_csv(path); print("wrote", path, len(df), "rows, total predicted", round(float(df["prediction"].sum())))
