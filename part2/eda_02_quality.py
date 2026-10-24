"""Part 2 EDA 2: column profile and data-quality checks of the emerging market tables."""
import polars as pl
pl.Config.set_tbl_rows(80); pl.Config.set_tbl_width_chars(200); pl.Config.set_fmt_str_lengths(60)
D = "data/public/../part2/emerging/"
def prof(df, name):
    rows = []
    for c, t in df.schema.items():
        s = df[c]
        r = dict(col=c, dtype=str(t), null=round(s.null_count() / len(df), 4), nuniq=s.n_unique())
        if t.is_numeric():
            r.update(min=s.min(), p50=s.median(), max=s.max())
        else:
            r["top"] = str(s.drop_nulls().value_counts(sort=True).head(3).rows())[:70]
        rows.append(r)
    print("\n###", name, df.shape); print(pl.DataFrame(rows, infer_schema_length=None))
for f in ("customers", "addresses", "policies_motor", "policies_buildings", "policies_contents", "claims"):
    prof(pl.read_parquet(D + f + ".parquet"), f)
