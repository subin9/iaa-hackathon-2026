"""Self-check for the Part 2 data-readiness deliverables.

Verifies that the deliverable set in ./outputs/ is complete, that
findings.json conforms to ./schemas/findings.schema.json, that the
modelling tables carry the required columns, and (if present) that the
baseline submission passes tools/check_sub.py. Format and presence only —
it does not judge content.

Run from anywhere: python tools/validate_outputs.py
Exit 0 = all checks pass; 1 = something to fix (listed on stdout).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PARQUET_MAGIC = b"PAR1"

CORE_TABLES = ["customers", "addresses", "weather", "policies_motor", "policies_buildings",
               "policies_contents", "claims", "test_motor", "test_buildings", "test_contents"]
OPTIONAL_TABLES = ["expenses", "reference_policies", "sample_submission"]
REQUIRED_MD = {
    "profile.md": None,
    "schema_mapping.md": None,
    "shift_report.md": None,
    "target_notes.md": None,
    "adaptation_decisions.md": ["Borrowed assumptions"],
    "retrospective.md": ["Rules I could not apply as written", "Judgment calls I am least sure about",
                         "Proposed additions"],
}
MT_REQUIRED = {"row_id", "policy_id", "split", "year", "exposure", "completion", "y"}

problems: list[str] = []
notes: list[str] = []


def problem(msg: str) -> None:
    problems.append(msg)


def is_parquet(p: Path) -> bool:
    return p.is_file() and p.read_bytes()[:4] == PARQUET_MAGIC


def check_markdown() -> None:
    for name, headings in REQUIRED_MD.items():
        p = OUT / name
        if not p.is_file():
            problem(f"{name}: missing")
            continue
        text = p.read_text(encoding="utf-8-sig")
        if not text.strip():
            problem(f"{name}: empty")
            continue
        for h in headings or []:
            if h.lower() not in text.lower():
                problem(f"{name}: section '{h}' not found (follow the template)")


def check_cleaned() -> None:
    d = OUT / "cleaned"
    if not d.is_dir():
        problem("cleaned/: directory missing — deliver every emerging table after treatment")
        return
    for t in CORE_TABLES:
        if not is_parquet(d / f"{t}.parquet"):
            problem(f"cleaned/{t}.parquet: missing or not parquet")
    for t in OPTIONAL_TABLES:
        if not (d / f"{t}.parquet").is_file():
            notes.append(f"cleaned/{t}.parquet not delivered (optional; copy through if untouched)")
    # schema parity with the as-delivered tables
    try:
        import pyarrow.parquet as pq
        for t in CORE_TABLES:
            src = ROOT / "data/emerging" / f"{t}.parquet"
            dst = d / f"{t}.parquet"
            if src.is_file() and is_parquet(dst):
                s_cols = pq.read_schema(src).names
                d_cols = pq.read_schema(dst).names
                missing = [c for c in s_cols if c not in d_cols]
                if missing:
                    problem(f"cleaned/{t}.parquet: columns dropped vs source: {missing}")
                extra = [c for c in d_cols if c not in s_cols]
                if extra:
                    notes.append(f"cleaned/{t}.parquet: extra columns {extra} (allowed if they are clearly named flags)")
    except ImportError:
        notes.append("pyarrow not installed — schema parity not checked")


def check_findings() -> None:
    p = OUT / "findings.json"
    if not p.is_file():
        problem("findings.json: missing")
        return
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        problem(f"findings.json: not valid JSON ({e})")
        return
    if not isinstance(data, list):
        problem("findings.json: top level must be a JSON array")
        return
    try:
        import jsonschema
    except ImportError:
        problem("findings.json: cannot validate — pip install jsonschema and rerun")
        return
    schema = json.loads((ROOT / "schemas/findings.schema.json").read_text(encoding="utf-8"))
    item = dict(schema["items"])
    item["$schema"] = schema.get("$schema", "https://json-schema.org/draft/2020-12/schema")
    v = jsonschema.Draft202012Validator(item)
    for i, entry in enumerate(data):
        fid = entry.get("finding_id", "no id") if isinstance(entry, dict) else "no id"
        for err in sorted(v.iter_errors(entry), key=lambda e: e.json_path)[:3]:
            problem(f"findings.json[{i}] ({fid}): {err.message} at {err.json_path}")
    if not data:
        notes.append("findings.json is an empty array — confirm that is intended")
    else:
        n_rules = sum(1 for e in data if isinstance(e, dict) and e.get("triggered_by_rules"))
        notes.append(f"findings.json: {len(data)} findings, {n_rules} attributed to playbook rules, "
                     f"{len(data) - n_rules} found without a rule")


def check_modelling_tables() -> None:
    d = OUT / "modelling_tables"
    if not d.is_dir():
        problem("modelling_tables/: directory missing")
        return
    try:
        import pyarrow.parquet as pq
    except ImportError:
        problem("modelling_tables/: pyarrow needed to check columns")
        return
    for line in ("motor", "buildings", "contents"):
        p = d / f"{line}.parquet"
        if not is_parquet(p):
            problem(f"modelling_tables/{line}.parquet: missing or not parquet")
            continue
        cols = set(pq.read_schema(p).names)
        missing = MT_REQUIRED - cols
        if missing:
            problem(f"modelling_tables/{line}.parquet: required columns missing {sorted(missing)}")


def check_baseline() -> None:
    d = OUT / "baseline"
    if not d.is_dir():
        notes.append("baseline/ not delivered (stretch deliverable)")
        return
    sub = d / "submission.csv"
    if not sub.is_file():
        problem("baseline/submission.csv: directory exists but file missing")
    else:
        r = subprocess.run([sys.executable, str(ROOT / "tools/check_sub.py"), str(sub), "--cleaned"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            problem("baseline/submission.csv failed check_sub:\n" + r.stdout.strip())
        else:
            notes.append("check_sub output:\n" + r.stdout.strip())
    if not (d / "validation.md").is_file():
        problem("baseline/validation.md: missing")
    hold = d / "holdout_2024.csv"
    if not hold.is_file():
        problem("baseline/holdout_2024.csv: missing (2023-only training -> every 2024 training row)")
    else:
        try:
            import polars as pl
            h = pl.read_csv(hold, schema_overrides={"row_id": pl.String, "prediction": pl.Float64})
            if set(h.columns) != {"row_id", "prediction"}:
                problem(f"holdout_2024.csv: columns must be row_id, prediction (got {h.columns})")
            elif h["prediction"].null_count() or not (h["prediction"] >= 0).all():
                problem("holdout_2024.csv: null or negative predictions")
            else:
                n2024 = 0
                for line in ("motor", "buildings", "contents"):
                    t = pl.read_parquet(ROOT / "data/emerging" / f"policies_{line}.parquet", columns=["row_id", "period_start"])
                    n2024 += t.filter(pl.col("period_start").cast(pl.Date).dt.year() == 2024).height
                if h["row_id"].n_unique() != h.height:
                    problem("holdout_2024.csv: duplicate row_ids")
                notes.append(f"holdout_2024.csv: {h.height:,} rows predicted; {n2024:,} 2024 training rows exist "
                             f"({h.height / max(n2024, 1):.1%} coverage)")
        except ImportError:
            notes.append("polars not installed - holdout file not checked")


def main() -> int:
    if not OUT.is_dir():
        print("FAIL: ./outputs/ does not exist")
        return 1
    check_markdown()
    check_cleaned()
    check_findings()
    check_modelling_tables()
    check_baseline()
    for n in notes:
        print("note:", n)
    if problems:
        print(f"FAIL — {len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("PASS — all deliverables present and schema-valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
