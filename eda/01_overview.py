import polars as pl, sys
D = "data/public/"
for f in ["customers","addresses","weather","policies_motor","policies_buildings","policies_contents","claims","test_motor","test_buildings","test_contents","sample_submission"]:
    df = pl.read_parquet(D+f+".parquet")
    print(f"\n### {f} {df.shape}")
    nulls = {c: n for c, n in zip(df.columns, df.null_count().row(0)) if n}
    print("dtypes:", dict(zip(df.columns, [str(t) for t in df.dtypes])))
    if nulls: print("nulls:", nulls)
    print(df.head(2))
