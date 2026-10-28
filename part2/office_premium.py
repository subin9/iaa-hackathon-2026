"""Office premium build-up for the 20 reference policies, on an annual basis.

Office premium P = (risk premium + fixed expense + catastrophe reinsurance) / (1 - variable expense - commission - premium tax - profit margin),
all rates from emerging/expenses.parquet (emerging column). Assumptions, stated in the report:
- the build-up is annual: the row's predicted cost is divided by its exposure, because written_premium is an annual figure (its mean does not
  change with the row's exposure in the training files) and the fixed expense is quoted per policy-year; the premium for the row's own period is
  P times exposure (column office_row);
- catastrophe reinsurance is a share of the risk premium of the property lines (buildings and contents), none for motor;
- commission follows the channel (direct 0%, broker 20%); the emerging market has no comparison-site commission.
usage: office_premium.py PRED.parquet OUT.csv   (PRED has row_id, prediction)"""
import sys; sys.path.insert(0, "part2")
import polars as pl
pred = pl.read_parquet(sys.argv[1]).select("row_id", "prediction")
ex = {r["item"]: r["emerging"] for r in pl.read_parquet("data/part2/emerging/expenses.parquet").iter_rows(named=True)}
ref = pl.read_parquet("data/part2/emerging/reference_policies.parquet").join(pred, on="row_id")
assert len(ref) == 20, len(ref)
comm = pl.col("channel").replace_strict({"direct": ex["commission_direct"], "broker": ex["commission_broker"]}, default=None)
d = ref.with_columns(commission_rate=comm)
assert d["commission_rate"].null_count() == 0, "a reference policy has a channel without a commission rate"
v, t, m = ex["variable_expense"], ex["premium_tax"], ex["target_profit_margin"]
d = d.with_columns(risk=pl.col("prediction") / pl.col("exposure"), fixed=pl.lit(ex["fixed_expense_per_policy"])
                   ).with_columns(cat_re=pl.when(pl.col("line") == "motor").then(0.0).otherwise(ex["cat_reinsurance"] * pl.col("risk"))
                   ).with_columns(office=(pl.col("risk") + pl.col("fixed") + pl.col("cat_re")) / (1 - v - pl.col("commission_rate") - t - m)
                   ).with_columns(variable=v * pl.col("office"), commission=pl.col("commission_rate") * pl.col("office"), tax=t * pl.col("office"), profit=m * pl.col("office"),
                                  office_row=pl.col("office") * pl.col("exposure"), vs_written=pl.col("office") / pl.col("written_premium"))
out = d.select("row_id", "line", "channel", "exposure", "risk", "fixed", "cat_re", "variable", "commission", "tax", "profit", "office", "office_row", "written_premium", "vs_written")
out.write_csv(sys.argv[2]); pl.Config.set_tbl_rows(25); pl.Config.set_tbl_width_chars(240); pl.Config.set_float_precision(2)
print(out); print("check: components add to the office premium:", bool(((out["risk"] + out["fixed"] + out["cat_re"] + out["variable"] + out["commission"] + out["tax"] + out["profit"] - out["office"]).abs().max() < 1e-6)))
