"""Build the control-arm workspace (Arm 0) next to the harness.

  python eval/make_cycle0.py            -> creates ../harness_bare/ (refuses if it exists)
  python eval/make_cycle0.py --force    -> replaces it

harness_bare/ = harness/ with the SAME charter structure, templates, schema,
tools, settings and data, but NO playbooks and NO registry. Its CLAUDE.md is
eval/cycle0_bare/CLAUDE.md (the harness charter with every playbook
reference removed). The agent is then run exactly as in LOOP.md Part A step
2, from harness_bare/, with the same kickoff_prompt.txt.

Held constant (so Arm 0 vs Arm B measures the playbooks): charter structure,
deliverables, templates, findings schema, tools, permissions, data, kickoff.
Differs: the 50 rules of Week 1 method and the registry.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "harness"
DST = ROOT / "harness_bare"
BARE_CHARTER = ROOT / "eval" / "cycle0_bare" / "CLAUDE.md"
EXCLUDE = {"playbooks", "memory", "outputs", "work", "__pycache__"}


def main() -> int:
    force = "--force" in sys.argv
    if DST.exists():
        if not force:
            print(f"{DST} exists; pass --force to replace")
            return 1
        shutil.rmtree(DST)
    DST.mkdir()
    for item in SRC.iterdir():
        if item.name in EXCLUDE:
            continue
        if item.is_dir():
            shutil.copytree(item, DST / item.name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(item, DST / item.name)
    (DST / "outputs").mkdir()
    (DST / "work").mkdir()
    shutil.copy2(BARE_CHARTER, DST / "CLAUDE.md")
    if "playbook" in (DST / "CLAUDE.md").read_text(encoding="utf-8").lower():
        print("bare charter still mentions playbooks — fix eval/cycle0_bare/CLAUDE.md")
        return 1
    print("harness_bare/ built:", sorted(p.name for p in DST.iterdir()))
    print("not copied:", sorted(EXCLUDE - {"outputs", "work", "__pycache__"}))
    print("Run from harness_bare/ with kickoff_prompt.txt. Operator must not open eval/answer_key.md before the run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
