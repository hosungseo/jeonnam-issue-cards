#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict

from common import ROOT, load_json, write_json


def load_optional(path):
    if not path.exists():
        return []
    return load_json(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    raw = load_optional(ROOT / "data" / "raw" / f"{args.date}.json")
    scored = load_optional(ROOT / "data" / "daily" / args.date / "scored.json")
    cards = load_optional(ROOT / "data" / "daily" / args.date / "cards.json")

    warnings = []
    source_counts = Counter(item.get("source_type", "unknown") for item in raw)
    region_counts = Counter(item.get("region", "unknown") for item in scored)
    category_counts = Counter(item.get("category", "general") for item in scored)

    if not raw:
        warnings.append("no raw items collected")
    if raw and not scored:
        warnings.append("raw items exist but no candidates survived scoring")
    if scored and not cards:
        warnings.append("scored candidates exist but no card specs were built")

    missing_source_url = [item.get("title", "UNKNOWN") for item in raw if not item.get("url")]
    if missing_source_url:
        warnings.append(f"raw items missing url: {len(missing_source_url)}")

    cluster_members = defaultdict(list)
    for item in scored:
        cluster_members[item.get("cluster_key", "unknown")].append(item.get("title", "UNKNOWN"))
    multi_source_clusters = {
        key: titles for key, titles in cluster_members.items() if len(titles) > 1
    }

    low_confidence_cards = [
        card.get("region", "UNKNOWN")
        for card in cards
        if card.get("confidence") not in {"high", "medium"}
    ]
    if low_confidence_cards:
        warnings.append(f"cards with unsupported confidence: {', '.join(low_confidence_cards)}")

    report = {
        "date": args.date,
        "counts": {
            "raw": len(raw),
            "scored": len(scored),
            "cards": len(cards),
        },
        "source_counts": dict(source_counts),
        "region_counts": dict(region_counts),
        "category_counts": dict(category_counts),
        "multi_source_clusters": multi_source_clusters,
        "warnings": warnings,
        "status": "warn" if warnings else "pass",
    }

    out = ROOT / "reports" / args.date / "pipeline_quality.json"
    write_json(out, report)
    print(f"pipeline audit {report['status']} ({len(warnings)} warnings) -> {out}")


if __name__ == "__main__":
    main()
