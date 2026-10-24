"""Put the developed-market modelling tables (work/{line}.parquet from src/prep.py) on the emerging-market coding,
so one model can be trained on developed rows and scored on emerging rows.

Maps: exact age -> age band, construction_type -> local code, occupation already clean. Developed-only columns
(exact age, mileage, telematics, credit band, customer age) are dropped. gender, self_employed and the
emerging region codes stay missing for developed rows (a market-specific recalibration step uses them later).
"""
import polars as pl

BAND = lambda c: (pl.when(pl.col(c) < 25).then(pl.lit("17-24")).when(pl.col(c) < 35).then(pl.lit("25-34"))
                  .when(pl.col(c) < 50).then(pl.lit("35-49")).when(pl.col(c) < 65).then(pl.lit("50-64")).otherwise(pl.lit("65+")))
# The developed construction_type is dirty: case variants (Brick, brick, BRICK) and a recode of timber from T (2021-22) to W (2023-25).
# Both letters are the timber category; mapping them apart would hand a model a year flag for buildings.
CONSTR = {"brick": "BRK", "stone": "STN", "t": "WOD", "w": "WOD", "non_standard": "MIX"}
DEV_ONLY = ["annual_mileage", "credit_band", "cust_age", "telematics_opt_in", "telematics_score"]


def main():
    for line in ("motor", "buildings", "contents"):
        d = pl.read_parquet(f"work/{line}.parquet")
        age = "driver_age" if line == "motor" else "policyholder_age"
        d = d.with_columns(**{f"{age}_band": BAND(age)}).drop(age)
        if "construction_type" in d.columns:
            d = d.with_columns(pl.col("construction_type").str.strip_chars().str.to_lowercase().replace_strict(CONSTR, default=None))
            assert d["construction_type"].null_count() == 0, "unmapped construction_type"
        d = d.drop([c for c in DEV_ONLY if c in d.columns]).with_columns(
            gender=pl.lit(None, dtype=pl.Utf8), self_employed=pl.lit(False))
        d.write_parquet(f"work/p2/dev_{line}.parquet")
        e = pl.read_parquet(f"work/p2/{line}.parquet")
        print(line, d.shape, "columns missing from dev:", sorted(set(e.columns) - set(d.columns)), "extra:", sorted(set(d.columns) - set(e.columns)))
        print("   age band share dev/em:", d[f"{age}_band"].value_counts(normalize=True).sort(f"{age}_band").rows(), e[f"{age}_band"].value_counts(normalize=True).sort(f"{age}_band").rows())


if __name__ == "__main__":
    main()
