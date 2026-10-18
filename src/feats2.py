"""Claim-network features, written to work/feats2_{line}.parquet keyed by row_id.

Uses only claims reported before each row's period_start, per customer:
- cust_repud_n: prior repudiated claims
- cust_badrep_n: prior claims through a repairer whose repudiation rate, over
  claims reported before the row, is above 10% with at least 30 claims
  (three repairers in the data handle about 700 claims each at 35%)
- cust_rep_rate_max: highest credibility-shrunk repudiation rate among the
  repairers on the customer's prior claims
- cust_tp_shared: prior claims whose third party also appears on another
  policy's claim before the row
"""
import polars as pl
from prep import LINES, load_claims
from feats import policy_map

K = 50  # credibility constant for repairer repudiation rates


def repairer_rates(c, cut):
    """Shrunk repudiation rate per repairer from claims reported before cut."""
    r = c.filter(pl.col("repairer_id").is_not_null() & (pl.col("report_date") < cut))
    p0 = (r["status"] == "repudiated").mean() or 0.0
    return r.group_by("repairer_id").agg(n=pl.len(), k=(pl.col("status") == "repudiated").sum()).with_columns(
        rate=(pl.col("k") + K * p0) / (pl.col("n") + K))


def build(line, claims, pmap):
    rows = pl.read_parquet(f"work/{line}.parquet", columns=["row_id", "customer_id", "period_start", "year"])
    c = claims.join(pmap.select("policy_id", "customer_id"), on="policy_id")
    out = []
    # repairer and third-party statistics are taken at 1 January of the row's year,
    # which is never later than the row's own period_start
    for y in rows["year"].unique().sort().to_list():
        cut = pl.date(y, 1, 1)
        rr = repairer_rates(c, cut)
        tp = c.filter(pl.col("third_party_id").is_not_null() & (pl.col("report_date") < cut)).group_by(
            "third_party_id").agg(tp_pol=pl.col("policy_id").n_unique())
        cy = c.join(rr.select("repairer_id", "rate", "n"), on="repairer_id", how="left").join(tp, on="third_party_id", how="left")
        ry = rows.filter(pl.col("year") == y)
        j = ry.join(cy.select("customer_id", "report_date", "status", "rate", "n", "tp_pol"), on="customer_id")
        j = j.filter(pl.col("report_date") < pl.col("period_start"))
        g = j.group_by("row_id").agg(
            cust_repud_n=(pl.col("status") == "repudiated").sum(),
            cust_badrep_n=((pl.col("rate") > 0.10) & (pl.col("n") >= 30)).sum(),
            cust_rep_rate_max=pl.col("rate").max(),
            cust_tp_shared=(pl.col("tp_pol") > 1).sum())
        out.append(ry.select("row_id").join(g, on="row_id", how="left"))
    out = pl.concat(out).with_columns(pl.col("cust_repud_n", "cust_badrep_n", "cust_tp_shared").fill_null(0))
    out.write_parquet(f"work/feats2_{line}.parquet")
    print(line, out.shape, out.select(pl.exclude("row_id").mean()).row(0, named=True), flush=True)


if __name__ == "__main__":
    claims, pmap = load_claims(), policy_map()
    for line in LINES:
        build(line, claims, pmap)
