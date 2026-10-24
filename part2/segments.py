"""Row segments of the emerging test set, shared by the probe builder and the probe solver.
A segment spec is a comma-separated list of key=value pairs, all of which must hold: line, nb (0/1), channel, gender, age (age band), region, and `all`."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import load, LINES


def test_frame(base: pl.DataFrame) -> pl.DataFrame:
    """base has row_id and prediction; returns one frame with the segment columns joined."""
    cols = []
    for l in LINES:
        t = load(l, "em").filter(pl.col("split") == "test")
        age = "driver_age_band" if l == "motor" else "policyholder_age_band"
        cols.append(t.select("row_id", line=pl.lit(l), nb=pl.col("new_business").cast(pl.Int8), channel="channel", gender="gender", age=pl.col(age), region="region"))
    return base.select("row_id", "prediction").join(pl.concat(cols), on="row_id")


def mask(d: pl.DataFrame, spec: str) -> np.ndarray:
    m = np.ones(len(d), bool)
    if spec == "all": return m
    for kv in spec.split(","):
        k, v = kv.split("="); col = d[k].to_numpy()
        m &= (col == int(v)) if k == "nb" else (col == v)
    return m
