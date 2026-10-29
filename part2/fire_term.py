"""Buildings fire on wildfire_index with the developed-market slope, added to a prior: lrp_fire += B (wildfire_index - training mean), written under a new
tag. The tree prior leaves weather out and is flat above the developed maximum of 0.635, where 22% of the 2025 buildings rows lie (e25_weather_peril.py).
usage: fire_term.py SRC_TAG DST_TAG [B]   (B defaults to 1.662, the developed Poisson slope of fire frequency on wildfire_index, 1,107 fires)"""
import sys
import polars as pl

src, dst = sys.argv[1], sys.argv[2]
B = float(sys.argv[3]) if len(sys.argv) > 3 else 1.662
for l in ["motor", "buildings", "contents"]:
    p = pl.read_parquet(f"work/p2/devperil{src}_{l}.parquet")
    if l == "buildings":
        t = pl.read_parquet(f"work/p2/{l}.parquet").select("row_id", "wildfire_index", "split")
        m = t.filter(pl.col("split") == "train")["wildfire_index"].mean()
        p = (p.join(t.select("row_id", "wildfire_index"), on="row_id", how="left")
              .with_columns(lrp_fire=pl.col("lrp_fire") + B * (pl.col("wildfire_index").fill_null(m) - m)).drop("wildfire_index"))
        print("training mean wildfire_index", round(m, 3), "rows", len(p))
    p.write_parquet(f"work/p2/devperil{dst}_{l}.parquet")
