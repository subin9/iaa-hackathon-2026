"""Build one modelling table per line for the emerging market (Part 2), in the same layout as src/prep.py.

What differs from the developed build (all found in part2/eda_*.py):
- Completion: the emerging market has only two training years, so no accident year is mature. Its report-lag
  percentiles match the developed market (median 9 days, 90th 44 to 46 days for motor), so the completion
  curves come from the developed claims of 2021-22 and are applied to the emerging rows.
- occupation is free text: trimmed, lower-cased, and "self-employed X" becomes X plus a self_employed flag.
- Ages come as bands, construction types as local codes: the table keeps them as they are; harmonise.py maps
  the developed market onto the same coding.
- No exact-repeat claims exist in the emerging claims file (604 in the developed one), the dedupe stays as a check.
"""
import numpy as np
import polars as pl
import prep

DEV, EM = "data/part2/developed/", "data/part2/emerging/"
LINES = {"motor": "M", "buildings": "B", "contents": "C"}


def clean_customers(cust):
    occ = pl.col("occupation").str.strip_chars().str.to_lowercase()
    return cust.drop("surname").with_columns(
        self_employed=occ.str.starts_with("self-employed").fill_null(False),
        occupation=occ.str.replace("^self-employed ", "").str.to_titlecase().str.replace("Care Worker", "Care worker")
        .str.replace("Retail Assistant", "Retail assistant").str.replace("Sales Representative", "Sales representative")
        .str.replace("Software Developer", "Software developer"))


def build(line, claims_em, G_all, G_by_peril):
    tr = pl.read_parquet(EM + f"policies_{line}.parquet").with_columns(split=pl.lit("train"))
    te = pl.read_parquet(EM + f"test_{line}.parquet").with_columns(split=pl.lit("test"))
    rows = pl.concat([tr.drop("renewal_decision"), te], how="diagonal_relaxed").with_columns(year=pl.col("period_start").dt.year())
    days = (pl.col("period_end") - pl.col("period_start")).dt.total_days() + 1
    rows = rows.with_columns(exposure_bad=((pl.col("exposure") - days / 365).abs() > 0.01), exposure=days / 365)
    if "sum_insured" in rows.columns:
        med = rows["sum_insured"].median()
        rows = rows.with_columns(si_bad=pl.col("sum_insured") > 100 * med).with_columns(
            sum_insured=pl.when(pl.col("si_bad")).then(pl.col("sum_insured") / 1000).otherwise(pl.col("sum_insured")))
    c = claims_em.filter(pl.col("line") == line)
    m = c.join(rows.select("row_id", "policy_id", "period_start", "period_end"), on="policy_id")
    m = m.filter(pl.col("loss_date").is_between(pl.col("period_start"), pl.col("period_end")))
    t = m.group_by("row_id").agg(y=pl.col("net").sum(), n=pl.len(), ymax=pl.col("net").max())
    rows = rows.join(t, on="row_id", how="left").with_columns(pl.col("y", "n", "ymax").fill_null(0))
    perils = sorted(c["peril"].unique().to_list())
    tp = m.group_by("row_id", "peril").agg(y=pl.col("net").sum(), n=pl.len()).pivot(on="peril", index="row_id", values=["y", "n"], separator="_")
    rows = rows.join(tp, on="row_id", how="left")
    rows = rows.with_columns(pl.col([f"{v}_{p}" for v in ("y", "n") for p in perils]).fill_null(0))
    for p in perils:
        rows = rows.with_columns(pl.Series(f"compc_{p}", prep.row_completion(rows, G_by_peril[(line, p, "count")])),
                                 pl.Series(f"compk_{p}", prep.row_completion(rows, G_by_peril[(line, p, "cost")])))
    comp = prep.row_completion(rows, G_all[line])
    rows = rows.with_columns(completion=pl.Series(comp)).with_columns(
        completion=pl.when(pl.col("split") == "test").then(1.0).otherwise(pl.col("completion")))
    cust = clean_customers(pl.read_parquet(EM + "customers.parquet"))
    addr = pl.read_parquet(EM + "addresses.parquet"); wx = pl.read_parquet(EM + "weather.parquet")
    rows = rows.join(cust, on="customer_id", how="left").join(addr, on="address_id", how="left").join(wx, on=["address_id", "year"], how="left")
    rows = rows.join(prep.history(claims_em, rows), on="row_id", how="left")
    return rows.with_columns(tenure_years=pl.col("year") - pl.col("customer_since_year"), property_age=pl.col("year") - pl.col("year_built"),
                             start_month=pl.col("period_start").dt.month(), premium_rate=pl.col("written_premium") / pl.col("exposure"))


def main():
    prep.D = DEV
    claims_dev = prep.load_claims()
    G_all = {l: prep.completion_curve(claims_dev, l) for l in LINES}
    G_by_peril = {}
    for l in LINES:
        for p in sorted(claims_dev.filter(pl.col("line") == l)["peril"].unique().to_list()):
            for by in ("count", "cost"):
                G_by_peril[(l, p, by)] = prep.completion_curve(claims_dev, l, p, by)
    prep.D = EM
    claims_em = prep.load_claims()
    print("emerging claims", len(pl.read_parquet(EM + "claims.parquet")), "after dedupe", len(claims_em))
    held = pl.concat([pl.read_parquet(EM + f"{f}_{l}.parquet", columns=["customer_id", "period_start"]).select(
        "customer_id", line=pl.lit(l), year=pl.col("period_start").dt.year()) for f in ("policies", "test") for l in LINES])
    nlines = held.unique().group_by("customer_id", "year").agg(n_lines=pl.col("line").n_unique())
    for line in LINES:
        rows = build(line, claims_em, G_all, G_by_peril).join(nlines, on=["customer_id", "year"], how="left")
        rows.write_parquet(f"work/p2/{line}.parquet")
        s = rows.filter(pl.col("split") == "train").group_by("year").agg(
            expo=pl.col("exposure").sum(), comp=(pl.col("completion") * pl.col("exposure")).sum() / pl.col("exposure").sum(),
            raw=pl.col("y").sum() / pl.col("exposure").sum(), adj=pl.col("y").sum() / (pl.col("exposure") * pl.col("completion")).sum(),
            n=pl.col("n").sum()).sort("year")
        print(line, rows.shape); print(s)


if __name__ == "__main__":
    main()
