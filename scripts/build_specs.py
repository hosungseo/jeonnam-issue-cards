#!/usr/bin/env python3
from __future__ import annotations

import argparse

from common import ROOT, load_json, short_source, write_json

CATEGORY_LABELS = {
    "safety": "안전·교통",
    "welfare": "복지·생활",
    "economy": "산업·예산",
    "agri_marine": "농수산·해양",
    "culture": "문화·관광",
    "general": "지역 이슈",
}


def summarize(item: dict) -> list[str]:
    body = item.get("body", "").strip()
    if len(body) <= 34:
        return [body]
    first = body[:34].rstrip() + "…"
    category = item.get("category")
    second_by_category = {
        "safety": "장마 전 점검이 시작됐습니다.",
        "welfare": "모집과 지원 일정이 열렸습니다.",
        "economy": "지역 예산과 일자리로 이어집니다.",
        "agri_marine": "현장 대응이 본격화됩니다.",
        "culture": "관광 동선 변화가 예고됐습니다.",
    }
    second = second_by_category.get(category, "후속 조치가 이어집니다.")
    return [first, second]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    scored = load_json(ROOT / "data" / "daily" / args.date / "scored.json")
    by_region = {}
    for item in scored:
        by_region.setdefault(item["region"], item)

    specs = []
    for region, item in sorted(by_region.items()):
        specs.append({
            "date": args.date,
            "region": region,
            "category": item["category"],
            "category_label": CATEGORY_LABELS.get(item["category"], "지역 이슈"),
            "headline": item["title"],
            "summary_lines": summarize(item),
            "source_urls": [item["url"]],
            "source_label": f"{item['source_name']} · {short_source(item['url'])}",
            "confidence": item["confidence"],
            "score": item["score"],
        })

    out = ROOT / "data" / "daily" / args.date / "cards.json"
    write_json(out, specs)
    print(f"built {len(specs)} card specs -> {out}")


if __name__ == "__main__":
    main()
