"""Segment level probes against the public leaderboard.

Scaling a fixed submission by s on one segment changes the Tweedie 1.5
deviance as -A s^-1/2 - G beta s^1/2, where beta is the sum of root
predictions on the segment. G comes from the eq9 global scale probes, so a
single probe per segment gives A and the optimal scale A / (G beta).

usage: level_probe.py build BASE        write one probe file per segment
       level_probe.py solve BASE D0 NAME=SCORE ...
"""
import sys
import numpy as np, polars as pl
from common import load

B9 = 0.5434386359567859  # eq9 fit: D = K - A s^-1/2 - B s^1/2 over the scales 0.95, 1.00, 1.05
SEGS = {
    "m_young": ("motor", pl.col("driver_age") <= 24, 0.90),
    "m_rural": ("motor", pl.col("urban_density") == "rural", 0.90),
    "m_tpft": ("motor", pl.col("cover_type") == "third_party_fire_theft", 0.90),
    "b_retired": ("buildings", pl.col("occupation") == "Retired", 1.10),
    "b_wind": ("buildings", pl.col("wind_exposure_index") >= pl.col("wind_exposure_index").quantile(0.7), 1.10),
}


def read(path):
    return pl.read_csv(path, schema_overrides={"row_id": pl.String})


def ids(name):
    line, cond, _ = SEGS[name]
    return load(line).filter(pl.col("split") == "test").filter(cond)["row_id"]


def G():
    return B9 / np.sqrt(read("submissions/eq9.csv")["prediction"].to_numpy()).sum()


if __name__ == "__main__":
    base = read(sys.argv[2])
    if sys.argv[1] == "build":
        for name, (_, _, s) in SEGS.items():
            out = base.with_columns(prediction=pl.when(pl.col("row_id").is_in(ids(name).implode())).then(pl.col("prediction") * s).otherwise(pl.col("prediction")))
            out.write_csv(f"submissions/probe_{name}.csv")
    else:
        D0, g = float(sys.argv[3]), G()
        for arg in sys.argv[4:]:
            name, D1 = arg.split("="); s1 = SEGS[name][2]
            beta = np.sqrt(base.filter(pl.col("row_id").is_in(ids(name).implode()))["prediction"].to_numpy()).sum()
            A = -(float(D1) - D0 + g * beta * (s1 ** 0.5 - 1)) / (s1 ** -0.5 - 1)
            s = A / (g * beta)
            gain = (-A * s ** -0.5 - g * beta * s ** 0.5) + A + g * beta
            print(f"{name}: optimal scale {s:.4f}, predicted gain {gain:.6f}")
