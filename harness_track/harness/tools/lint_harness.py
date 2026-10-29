"""Harness lint: every rule anchor in playbooks has a registry entry and vice versa.

Run: python tools/lint_harness.py   (exit 1 on any mismatch)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = re.compile(r"<!--\s*rule:\s*(R-\d{4})\s*-->")
ENTRY = re.compile(r"^- id:\s*(R-\d{4})\s*$", re.M)
LOC = re.compile(r"^- id:\s*(R-\d{4})\s*$(?:.|\n)*?^  location:\s*(\S+)", re.M)


def main() -> int:
    problems = []
    anchors: dict[str, str] = {}
    for f in sorted((ROOT / "playbooks").glob("*.md")):
        for rid in ANCHOR.findall(f.read_text(encoding="utf-8")):
            if rid in anchors:
                problems.append(f"{rid} anchored twice ({anchors[rid]}, {f.name})")
            anchors[rid] = f"playbooks/{f.name}"
    reg_text = (ROOT / "memory/registry.yaml").read_text(encoding="utf-8")
    entries = ENTRY.findall(reg_text)
    if len(entries) != len(set(entries)):
        problems.append("duplicate ids in registry")
    locations = {}
    for block in re.split(r"\n(?=- id:)", reg_text):
        m_id = re.search(r"- id:\s*(R-\d{4})", block)
        m_loc = re.search(r"^\s*location:\s*(\S+)", block, re.M)
        if m_id and m_loc:
            locations[m_id.group(1)] = m_loc.group(1)
    for rid in sorted(set(entries) - set(anchors)):
        problems.append(f"{rid} in registry but not anchored in any playbook")
    for rid in sorted(set(anchors) - set(entries)):
        problems.append(f"{rid} anchored in {anchors[rid]} but missing from registry")
    for rid, loc in locations.items():
        if rid in anchors and anchors[rid] != loc:
            problems.append(f"{rid} location says {loc} but anchor is in {anchors[rid]}")
    if problems:
        print(f"FAIL — {len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print(f"PASS — {len(entries)} rules, anchors and registry agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
