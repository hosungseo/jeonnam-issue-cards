#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import ROOT, load_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    specs = load_json(ROOT / "data" / "daily" / args.date / "cards.json")
    errors = []
    for spec in specs:
        for field in ["date", "region", "headline", "summary_lines", "source_urls", "confidence"]:
            if not spec.get(field):
                errors.append(f"{spec.get('region','UNKNOWN')}: missing {field}")
        if len(spec["headline"]) > 46:
            errors.append(f"{spec['region']}: headline too long")
        if any(len(line) > 58 for line in spec["summary_lines"]):
            errors.append(f"{spec['region']}: summary line too long")
        png = ROOT / "cards" / args.date / f"{spec['region']}.png"
        if not png.exists():
            errors.append(f"{spec['region']}: missing png")

    report = {
        "date": args.date,
        "card_count": len(specs),
        "errors": errors,
        "status": "pass" if not errors else "fail",
    }
    out = ROOT / "reports" / args.date / "qc.json"
    write_json(out, report)
    print(f"qc {report['status']} ({len(errors)} errors) -> {out}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

