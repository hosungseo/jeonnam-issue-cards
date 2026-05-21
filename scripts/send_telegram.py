#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import ROOT, load_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    specs = load_json(ROOT / "data" / "daily" / args.date / "cards.json")
    lines = [f"전남 주요 이슈 카드뉴스 {args.date}", f"카드 {len(specs)}장"]
    for spec in specs:
        lines.append(f"- {spec['region']}: {spec['headline']} ({spec['category_label']})")

    report = ROOT / "reports" / args.date / "telegram.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if args.send:
        raise SystemExit("real Telegram sending is handled by OpenClaw message tool, not this dry-run script")
    print(report.read_text(encoding="utf-8"))
    print(f"dry-run payload -> {report}")


if __name__ == "__main__":
    main()

