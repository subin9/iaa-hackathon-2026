"""Part 2 EDA 5: one-way relativities by rating factor, developed vs emerging (completion-adjusted cost per exposure, relative to the line mean)."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import *
pl.Config.set_tbl_rows(100); pl.Config.set_tbl_width_chars(160)
def binned(df, c, k=6):
    s = df[c]
    if s.dtype.is_numeric() and s.n_unique() > 12:
        e = np.unique(np.quantile(s.drop_nulls().to_numpy(), np.linspace(0, 1, k + 1)[1:-1]))
        v = s.to_numpy().astype(float)
        return pl.Series(np.where(np.isnan(v), "NA", np.char.add("q", np.searchsorted(e, v).astype(str)))) if False else pl.Series([("NA" if (x is None or np.isnan(x)) else f"q{int(np.searchsorted(e, x))}") for x in v])
    return s.cast(pl.Utf8).fill_null("NA")
def oneway(df, c):
    t = df.with_columns(lvl=binned(df, c)).group_by("lvl").agg(w=(pl.col("exposure") * pl.col("completion")).sum(), y=pl.col("y").sum(), n=pl.col("n").sum())
    r = t["y"].sum() / t["w"].sum()
    return t.with_columns(rel=pl.col("y") / pl.col("w") / r).select("lvl", "w", "n", "rel").sort("lvl")
FACT = {"motor": ["driver_age_band", "ncb_years", "years_licensed", "vehicle_value_group", "vehicle_age", "cover_type", "vehicle_use", "overnight_parking", "named_young_driver", "voluntary_excess", "urban_density", "prior_claims_5y", "licence_points", "fuel_type", "body_type", "channel", "payment_method", "new_business", "written_premium"],
        "buildings": ["policyholder_age_band", "sum_insured", "construction_type", "occupancy", "property_age", "flood_zone", "distance_to_river_km", "soil_type", "roof_type", "basement", "trees_within_5m", "urban_density", "accidental_damage_cover", "days_unoccupied", "channel", "new_business", "written_premium"],
        "contents": ["policyholder_age_band", "sum_insured", "tenure", "security_level", "high_value_items", "accidental_damage_cover", "works_from_home", "lodgers", "bicycle_cover", "urban_density", "flood_zone", "channel", "new_business", "written_premium"]}
line = sys.argv[1]; facs = sys.argv[2:] or FACT[line]
dev = load(line, "dev").filter(pl.col("split") == "train"); em = load(line, "em").filter(pl.col("split") == "train")
for c in facs:
    a, b = oneway(dev, c), oneway(em, c)
    j = a.join(b, on="lvl", how="full", coalesce=True).sort("lvl")
    print(f"\n--- {line} {c}   (dev rel | em rel, em claims)"); print(j.select("lvl", dev_rel=pl.col("rel").round(2), dev_n="n", em_rel=pl.col("rel_right").round(2), em_n="n_right"))
