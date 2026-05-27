#!/usr/bin/env python3
"""Print the synthetic fixture path; optionally clone it to a new period.

Usage:
    python scripts/seed_synthetic_tenant.py            # show base fixture
    python scripts/seed_synthetic_tenant.py 2026-05    # clone to a new period
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIX = REPO_ROOT / "data/fixtures"


def main():
    base = FIX / "synthetic_report_2026-04.json"
    print("Synthetic base fixture:", base)
    if len(sys.argv) > 1:
        new_period = sys.argv[1]
        data = json.loads(base.read_text(encoding="utf-8"))
        data["period"] = new_period
        out = FIX / f"synthetic_report_{new_period}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Wrote", out)


if __name__ == "__main__":
    main()
