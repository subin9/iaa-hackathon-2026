"""Build one modelling table per line: features, target, completion factor.

Target y: sum over claims with loss_date inside the row period of
incurred_to_date - recoveries (repudiated claims carry zero, so they drop out).

Completion: share of a row's ultimate cost that is already reported at the
31 Dec 2024 valuation. It comes from cost-weighted report-lag curves of mature
accident years (2021-2022), mixed over perils by their cost share, and averaged
over the days of the row period. Open case estimates are taken at face value.
"""
import numpy as np
import polars as pl

D = "data/public/"
VAL = pl.date(2024, 12, 31)
LINES = {"motor": "M", "buildings": "B", "contents": "C"}
MAXAGE = 1500


def load_claims():
    # 604 claims repeat another claim exactly (policy, peril, loss date, amount) under a new id
    c = pl.read_parquet(D + "claims.parquet")
    c = c.unique(["policy_id", "peril", "loss_date", "incurred_to_date", "recoveries"], keep="first", maintain_order=True)
    return c.with_columns(
        net=pl.col("incurred_to_date") - pl.col("recoveries"),
        lag=(pl.col("report_date") - pl.col("loss_date")).dt.total_days(),
    )


def completion_curve(claims, line, peril=None, by="cost"):
    """G(age) for age 0..MAXAGE days: expected reported share of ultimate cost (or count)."""
    c = claims.filter((pl.col("line") == line) & pl.col("loss_date").dt.year().is_between(2021, 2022))
    if peril:
        c = c.filter(pl.col("peril") == peril)
    # cap each claim at the 99.5th percentile so one large claim does not set the curve
    cap = c["net"].quantile(0.995)
    c = c.with_columns(w=pl.col("net").clip(upper_bound=cap) if by == "cost" else pl.lit(1.0))
    lag = c["lag"].to_numpy()
    w = c["w"].to_numpy()
    hist = np.bincount(np.clip(lag, 0, MAXAGE), weights=w, minlength=MAXAGE + 1)
    return np.cumsum(hist) / w.sum()


def row_completion(df, G):
    """Mean of G over loss ages of the row's days (loss assumed uniform in the period)."""
    H = np.concatenate([[0.0], np.cumsum(G)])  # H[k] = sum G[0..k-1]
    a_lo = (VAL - pl.col("period_end")).dt.total_days()
    a_hi = (VAL - pl.col("period_start")).dt.total_days()
    lo = np.clip(df.select(a_lo).to_series().to_numpy(), 0, MAXAGE)
    hi = np.clip(df.select(a_hi).to_series().to_numpy(), 0, MAXAGE)
    return (H[hi + 1] - H[lo]) / (hi - lo + 1)


def history(claims, rows):
    """Claim counts and cost before each row's period_start, by policy and by customer.

    Uses only claims reported before period_start, which is what an insurer
    knows at renewal. Works for 2025 test rows the same way.
    """
    pol = claims.select("policy_id", "line", "report_date", "net")
    cust_map = pl.concat(
        [pl.read_parquet(D + f"{f}_{l}.parquet", columns=["policy_id", "customer_id"])
         for f in ("policies", "test") for l in LINES]
    ).unique("policy_id")
    cust = pol.join(cust_map, on="policy_id")
    out = rows.select("row_id", "policy_id", "customer_id", "period_start")
    for key, src, name in [("policy_id", pol, "pol"), ("customer_id", cust, "cust")]:
        j = out.select("row_id", key, "period_start").join(src.select(key, "report_date", "net"), on=key)
        j = j.filter(pl.col("report_date") < pl.col("period_start"))
        g = j.group_by("row_id").agg(
            pl.len().alias(f"{name}_nclaims"),
            pl.col("net").sum().alias(f"{name}_cost"),
            (pl.col("report_date") >= pl.col("period_start").dt.offset_by("-1y")).sum().alias(f"{name}_nclaims_1y"),
        )
        out = out.join(g, on="row_id", how="left")
    return out.drop("policy_id", "customer_id", "period_start").fill_null(0)


def build(line, claims):
    tr = pl.read_parquet(D + f"policies_{line}.parquet").with_columns(split=pl.lit("train"))
    te = pl.read_parquet(D + f"test_{line}.parquet").with_columns(split=pl.lit("test"))
    rows = pl.concat([tr.drop("renewal_decision"), te], how="diagonal_relaxed")
    rows = rows.with_columns(year=pl.col("period_start").dt.year())
    # exposure has rows in days (up to 365) and on a 360-day basis; rebuild it from the dates
    days = (pl.col("period_end") - pl.col("period_start")).dt.total_days() + 1
    rows = rows.with_columns(exposure_bad=((pl.col("exposure") - days / 365).abs() > 0.01), exposure=days / 365)
    if "sum_insured" in rows.columns:
        # about 0.1% of sums insured are 1000x too large (keyed in a different unit)
        med = rows["sum_insured"].median()
        rows = rows.with_columns(si_bad=pl.col("sum_insured") > 100 * med).with_columns(
            sum_insured=pl.when(pl.col("si_bad")).then(pl.col("sum_insured") / 1000).otherwise(pl.col("sum_insured")))

    # target
    c = claims.filter(pl.col("line") == line)
    m = c.join(rows.select("row_id", "policy_id", "period_start", "period_end"), on="policy_id")
    m = m.filter(pl.col("loss_date").is_between(pl.col("period_start"), pl.col("period_end")))
    t = m.group_by("row_id").agg(y=pl.col("net").sum(), n=pl.len(), ymax=pl.col("net").max())
    rows = rows.join(t, on="row_id", how="left").with_columns(pl.col("y", "n", "ymax").fill_null(0))
    tp = m.group_by("row_id", "peril").agg(y=pl.col("net").sum(), n=pl.len()).pivot(
        on="peril", index="row_id", values=["y", "n"], separator="_")
    rows = rows.join(tp, on="row_id", how="left")
    perils = sorted(c["peril"].unique().to_list())
    rows = rows.with_columns(pl.col([f"{v}_{p}" for v in ("y", "n") for p in perils]).fill_null(0))
    for p in perils:
        rows = rows.with_columns(
            pl.Series(f"compc_{p}", row_completion(rows, completion_curve(claims, line, p, "count"))),
            pl.Series(f"compk_{p}", row_completion(rows, completion_curve(claims, line, p, "cost"))))

    G = completion_curve(claims, line)
    comp = row_completion(rows, G)
    rows = rows.with_columns(completion=pl.Series(comp)).with_columns(
        completion=pl.when(pl.col("split") == "test").then(1.0).otherwise(pl.col("completion")))

    # joins
    cust = pl.read_parquet(D + "customers.parquet").drop("surname")
    addr = pl.read_parquet(D + "addresses.parquet")
    wx = pl.read_parquet(D + "weather.parquet")
    rows = (rows.join(cust, on="customer_id", how="left")
                .join(addr, on="address_id", how="left")
                .join(wx, on=["address_id", "year"], how="left"))
    rows = rows.join(history(claims, rows), on="row_id", how="left")

    rows = rows.with_columns(
        cust_age=(pl.col("period_start") - pl.col("date_of_birth")).dt.total_days() / 365.25,
        tenure_years=pl.col("year") - pl.col("customer_since_year"),
        property_age=pl.col("year") - pl.col("year_built"),
        start_month=pl.col("period_start").dt.month(),
        premium_rate=pl.col("written_premium") / pl.col("exposure"),
        n_lines=pl.lit(0),  # filled below
    ).drop("date_of_birth")
    return rows, G


def main():
    claims = load_claims()
    held = pl.concat([pl.read_parquet(D + f"{f}_{l}.parquet", columns=["customer_id", "period_start"]).select(
        "customer_id", line=pl.lit(l), year=pl.col("period_start").dt.year())
        for f in ("policies", "test") for l in LINES])
    nlines = held.unique().group_by("customer_id", "year").agg(n_lines=pl.col("line").n_unique())
    for line in LINES:
        rows, G = build(line, claims)
        rows = rows.drop("n_lines").join(nlines, on=["customer_id", "year"], how="left")
        rows.write_parquet(f"work/{line}.parquet")
        np.save(f"work/G_{line}.npy", G)
        s = rows.filter(pl.col("split") == "train").group_by("year").agg(
            expo=pl.col("exposure").sum(), comp=(pl.col("completion") * pl.col("exposure")).sum() / pl.col("exposure").sum(),
            raw=pl.col("y").sum() / pl.col("exposure").sum(),
            adj=pl.col("y").sum() / (pl.col("exposure") * pl.col("completion")).sum()).sort("year")
        print(line, rows.shape, "G at 30/90/365d:", G[30].round(3), G[90].round(3), G[365].round(3))
        print(s)


if __name__ == "__main__":
    main()
