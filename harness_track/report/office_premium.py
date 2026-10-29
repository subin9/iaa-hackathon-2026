"""Office-premium build-up for the 20 reference policies (Part 2 report requirement).

Usage:  python report/office_premium.py <submission.csv> [--out report/office_premium.md]

Risk premium = the row's predicted expected ultimate claim cost from the submission file (a row total for the
row's exposure, net of excess and recoveries). Loadings from emerging/expenses.parquet:

  cat            = cat_reinsurance x risk premium            (property lines only; "share of property risk premium")
  fixed          = fixed_expense_per_policy x exposure       (per policy-year, pro-rated to the row's exposure)
  variable, commission(channel), premium tax, profit margin  = shares of the OFFICE premium

  office premium P solves   P = risk + cat + fixed + (variable + commission + tax + profit) x P
                            P = (risk + cat + fixed) / (1 - variable - commission - tax - profit)

Assumptions stated in the output: fixed expense pro-rated by exposure; comparison-site commission is undefined for
the emerging market (null) and is taken as the developed market's 10 % with a flag (finding F-19 / R-0412).
"""
from __future__ import annotations
import sys
from pathlib import Path
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "week2_data" / "emerging"


def main(argv):
    if not argv:
        print(__doc__); return 1
    sub_path = Path(argv[0]); out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else ROOT / "report" / "office_premium.md"
    exp = {r["item"]: r for r in pl.read_parquet(E / "expenses.parquet").to_dicts()}
    fixed = exp["fixed_expense_per_policy"]["emerging"]; var = exp["variable_expense"]["emerging"]
    tax = exp["premium_tax"]["emerging"]; cat = exp["cat_reinsurance"]["emerging"]; profit = exp["target_profit_margin"]["emerging"]
    comm = {"direct": exp["commission_direct"]["emerging"], "broker": exp["commission_broker"]["emerging"],
            "comparison_site": exp["commission_comparison_site"]["emerging"]}
    comm_flag = comm["comparison_site"] is None
    if comm_flag:
        comm["comparison_site"] = exp["commission_comparison_site"]["developed"]
    ref = pl.read_parquet(E / "reference_policies.parquet").with_columns(pl.col("row_id").cast(pl.String))
    sub = pl.read_csv(sub_path, schema_overrides={"row_id": pl.String, "prediction": pl.Float64})
    df = ref.join(sub, on="row_id", how="left")
    assert df["prediction"].null_count() == 0, "reference row_ids missing from the submission file"
    rows = []
    for r in df.select("row_id", "line", "exposure", "channel", "new_business", "prediction").to_dicts():
        risk = r["prediction"]; is_prop = r["line"] in ("buildings", "contents")
        cat_load = cat * risk if is_prop else 0.0
        fixed_load = fixed * r["exposure"]
        c = comm[r["channel"]]
        denom = 1 - var - c - tax - profit
        office = (risk + cat_load + fixed_load) / denom
        rows.append({**r, "cat": cat_load, "fixed": fixed_load, "commission_rate": c, "variable": var * office,
                     "commission": c * office, "tax": tax * office, "profit": profit * office, "office": office,
                     "office_per_year": office / r["exposure"], "loading_ratio": office / risk})
    t = pl.DataFrame(rows)
    lines = [f"# Office premium build-up — 20 reference policies\n",
             f"Risk premiums from `{sub_path.name}`. Loadings from `expenses.parquet` (emerging): fixed {fixed:.0f} CU per policy-year "
             f"(pro-rated by exposure), variable {var:.0%}, commission direct {comm['direct']:.0%} / broker {comm['broker']:.0%} / "
             f"comparison site {comm['comparison_site']:.0%}{' (undefined for the emerging market — developed value assumed, team query F-19)' if comm_flag else ''}, "
             f"premium tax {tax:.0%}, cat reinsurance {cat:.0%} of property risk premium, target profit {profit:.0%}.\n",
             "Office premium P = (risk + cat + fixed) / (1 − variable − commission − tax − profit). All CU, row totals for the row's exposure.\n",
             "| row_id | line | exposure | channel | NB | risk premium | + cat | + fixed | = net cost | office premium | per year | office / risk |",
             "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in t.sort(["line", "row_id"]).to_dicts():
        lines.append(f"| {r['row_id']} | {r['line']} | {r['exposure']:.4f} | {r['channel']} | {'Y' if r['new_business'] else 'N'} | "
                     f"{r['prediction']:,.2f} | {r['cat']:,.2f} | {r['fixed']:,.2f} | {r['prediction']+r['cat']+r['fixed']:,.2f} | "
                     f"**{r['office']:,.2f}** | {r['office_per_year']:,.2f} | {r['loading_ratio']:.2f} |")
    g = t.group_by("line").agg(pl.col("prediction").sum().alias("risk"), pl.col("office").sum().alias("office"), pl.len().alias("n")).sort("line")
    lines.append("\nTotals by line: " + "; ".join(f"{r['line']} n={r['n']} risk {r['risk']:,.0f} → office {r['office']:,.0f} (×{r['office']/r['risk']:.2f})" for r in g.to_dicts()))
    lines.append("\nWorked example (first motor row): office = (risk + 0 + 85 × exposure) / (1 − 0.15 − commission − 0.08 − 0.08); for a broker policy the denominator is 1 − 0.15 − 0.20 − 0.08 − 0.08 = 0.49, so every CU of net cost needs 2.04 CU of office premium; a direct policy's denominator is 0.69.")
    lines.append("\nNotes: (1) the risk premium is the model's expected ultimate claim cost for the row — it already includes IBNR completion, the trend decision and the new-business relativity (report/decisions_B.md); (2) cat reinsurance applies to property risk premium only, as the expenses table states; (3) a very short row (exposure 0.07–0.33) carries a pro-rated fixed expense — if the insurer charges the fixed expense per policy regardless of term, those rows' office premiums rise by (1 − exposure) × 85 / denominator.")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}"); print("\n".join(lines[3:8])); print("...")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
