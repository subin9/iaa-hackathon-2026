"""Part 2 EDA 6: do the weather columns drive the weather perils, in each market? One-way cost rate by weather quintile (relative to the peril mean)."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import *
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_width_chars(200)
PAIRS = [("motor", "glass_hail", ["hail_days", "wind_exposure_index"]), ("buildings", "storm", ["wind_exposure_index", "hail_days"]), ("buildings", "escape_of_water", ["freezing_days", "mean_temperature_c"]),
         ("buildings", "subsidence", ["dry_summer_index", "rainfall_mm"]), ("buildings", "flood", ["rainfall_mm", "flood_zone", "distance_to_river_km"]), ("contents", "flood", ["rainfall_mm", "flood_zone"]),
         ("contents", "escape_of_water", ["freezing_days"]), ("buildings", "fire", ["wildfire_index"])]
for line, peril, cols in PAIRS:
    for c in cols:
        out = {}
        for mk in ("dev", "em"):
            df = load(line, mk).filter(pl.col("split") == "train")
            v = df[c].to_numpy().astype(float); ok = ~np.isnan(v); e = np.unique(np.quantile(v[ok], np.linspace(0, 1, 6)[1:-1]))
            q = np.where(ok, np.searchsorted(e, v), -1)
            w = df["exposure"].to_numpy() * df[f"compk_{peril}"].to_numpy(); y = df[f"y_{peril}"].to_numpy(); r0 = y.sum() / w.sum()
            out[mk] = [round((y[q == k].sum() / w[q == k].sum()) / r0, 2) if (q == k).sum() else None for k in range(len(e) + 1)] + [f"range {np.nanmin(v):.1f}..{np.nanmax(v):.1f} med {np.nanmedian(v):.1f}"]
        print(f"{line:9s} {peril:16s} {c:22s} dev {out['dev']}\n{'':50s} em  {out['em']}")
