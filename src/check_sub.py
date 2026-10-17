"""Guardrails for a submission file: ids, values, and level against history."""
import sys
import polars as pl
from common import LINES, load

sub = pl.read_csv(sys.argv[1], schema_overrides={"row_id": pl.String})
ss = pl.read_parquet("data/public/sample_submission.parquet")
assert sub.height == ss.height and sub["row_id"].n_unique() == sub.height, "row count or duplicates"
assert set(sub["row_id"]) == set(ss["row_id"]), "row ids differ from sample_submission"
assert sub["prediction"].is_null().sum() == 0 and (sub["prediction"] >= 0).all(), "null or negative"
for line in LINES:
    df = load(line)
    te = df.filter(pl.col("split") == "test").join(sub, on="row_id")
    hist = df.filter(pl.col("split") == "train").group_by("year").agg(
        rate=pl.col("y").sum() / (pl.col("exposure") * pl.col("completion")).sum()).sort("year")
    print(f"{line}: 2025 predicted rate {te['prediction'].sum() / te['exposure'].sum():.1f} | history",
          dict(zip(hist["year"], hist["rate"].round(1))), "| max", round(te["prediction"].max(), 1))
print("ok", sub.height, "rows")
