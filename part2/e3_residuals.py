"""E3: A/E of the level-calibrated developed prior (M1) on emerging 2023-24 rows by segment, with a sandwich z-score per segment.
Large |z| marks a factor whose effect in the emerging market differs from the developed one."""
import sys; sys.path.insert(0, "part2")
import numpy as np, polars as pl
from lib import *
pl.Config.set_tbl_rows(200); pl.Config.set_tbl_width_chars(170)
SEG = {"motor": ["year", "region", "gender", "channel", "new_business", "driver_age_band", "urban_density", "payment_method", "self_employed", "cover_type", "marital_status", "fuel_type", "overnight_parking", "vehicle_use", "named_young_driver", "marketing_segment", "campaign_code", "occupation", "ncb_years", "years_licensed", "vehicle_value_group", "vehicle_age", "annual_mileage_na"],
       "buildings": ["year", "region", "gender", "channel", "new_business", "policyholder_age_band", "urban_density", "construction_type", "occupancy", "flood_zone", "soil_type", "roof_type", "basement", "trees_within_5m", "property_type", "energy_rating", "listed_building", "solar_panels", "accidental_damage_cover", "bedrooms", "payment_method", "self_employed", "marketing_segment"],
       "contents": ["year", "region", "gender", "channel", "new_business", "policyholder_age_band", "urban_density", "tenure", "security_level", "high_value_items", "accidental_damage_cover", "works_from_home", "lodgers", "bicycle_cover", "flood_zone", "payment_method", "self_employed", "marketing_segment", "occupation"]}
def tab(df, c):
    s = df[c]
    if s.dtype.is_numeric() and s.n_unique() > 8:
        e = np.unique(np.quantile(s.drop_nulls().to_numpy(), np.linspace(0, 1, 6)[1:-1])); v = s.to_numpy().astype(float)
        lv = pl.Series([("NA" if np.isnan(x) else f"q{int(np.searchsorted(e, x))}") for x in v])
    else:
        lv = s.cast(pl.Utf8).fill_null("NA")
    t = df.with_columns(lvl=lv).group_by("lvl").agg(n=pl.col("n").sum(), A=pl.col("y").sum(), E=pl.col("mu").sum(), ss=((pl.col("y") - pl.col("mu")) ** 2).sum())
    return t.with_columns(AE=pl.col("A") / pl.col("E"), z=(pl.col("A") - pl.col("E")) / pl.col("ss").sqrt()).sort("lvl")
rows = []
for line in LINES:
    em = load(line, "em").filter(pl.col("split") == "train").join(pl.read_parquet(f"work/p2/devprior_{line}.parquet"), on="row_id")
    mu0 = np.exp(em["lr_dev"].to_numpy()) * offset(em); k = em["y"].sum() / mu0.sum()
    em = em.with_columns(mu=pl.Series(mu0 * k), annual_mileage_na=pl.lit(0))
    print(f"\n######## {line}: level factor k = {k:.3f}; by year:", tab(em, "year").select("lvl", "n", AE=pl.col("AE").round(3), z=pl.col("z").round(1)).rows())
    for c in SEG[line]:
        if c not in em.columns: continue
        t = tab(em, c)
        for r in t.iter_rows(named=True):
            rows.append(dict(line=line, factor=c, level=r["lvl"], n=r["n"], AE=round(r["AE"], 3), z=round(r["z"], 1)))
big = pl.DataFrame(rows).filter(pl.col("z").abs() >= 2.0).with_columns(az=pl.col("z").abs()).sort("az", descending=True).drop("az")
print("\n==== segments with |z| >= 2 (A/E of the level-calibrated dev prior):"); print(big.head(60))
print("segments tested:", len(rows), " with |z|>=2:", len(big), "(about 5% =", round(0.05 * len(rows)), "expected by chance)")
