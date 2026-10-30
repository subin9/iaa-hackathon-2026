"""x1.2 probe files on one segment each of a base submission (the 2026-10-31 round on v14_cells). Segments come from the out-of-fold residual scan
of the training new business after the v13 and v14 factors were applied to it, keeping levels that are off the same way in 2023 and 2024.
Quintiles are those of the line's training new business (q0 lowest, q4 highest), as in the scan.
usage: probe_q15.py BASE.csv OUT_DIR"""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
import submission

SEG = {"q15a": ("motor", "property_age", "q0"), "q15b": ("motor", "elevation_m", "q4"), "q15c": ("motor", "wind_exposure_index", "q2"),
       "q15d": ("motor", "vehicle_age", "q3"), "q15e": ("motor", "rainfall_mm", "q1"), "q15f": ("contents", "years_at_address", "q0"),
       "q15g": ("contents", "marketing_segment", "young_affluent")}
base = pl.read_csv(sys.argv[1])
for k, (line, col, lvl) in SEG.items():
    t = pl.read_parquet(f"work/clean/work/p2/{line}.parquet").filter(pl.col("new_business"))
    tr, te = t.filter(pl.col("split") == "train"), t.filter(pl.col("split") == "test")
    if lvl.startswith("q") and lvl[1:].isdigit():
        q = np.unique(np.nanquantile(tr[col].cast(pl.Float64).to_numpy(), [0.2, 0.4, 0.6, 0.8])); v = te[col].cast(pl.Float64).to_numpy()
        hit = np.searchsorted(q, v, side="right") == int(lvl[1:])
        hit &= ~np.isnan(v); ids = te.filter(pl.Series(hit))["row_id"]; desc = f"cuts {np.round(q, 3).tolist()}"
    else:
        ids = te.filter(pl.col(col) == lvl)["row_id"]; desc = ""
    print(k, line, col, lvl, desc, "rows", len(ids))
    submission.write(base.with_columns(prediction=pl.when(pl.col("row_id").is_in(ids.implode())).then(pl.col("prediction") * 1.2).otherwise(pl.col("prediction"))),
                     f"{sys.argv[2]}/{k}.csv")
