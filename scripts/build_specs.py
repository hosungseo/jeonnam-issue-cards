#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re

from common import ROOT, load_json, short_source, write_json


def _clean_body(body: str) -> str:
    """Flatten whitespace/bullets from board or RSS body text."""
    text = re.sub(r"\s+", " ", body.replace("\r", " ").replace("\n", " "))
    text = re.sub(r"^[-·•\s]+", "", text)
    return text.strip()


def _lead_sentence(body: str, limit: int = 50) -> str:
    """Take a clean lead snippet, cutting on a word/clause boundary."""
    body = _clean_body(body)
    if len(body) <= limit:
        return body
    cut = body[:limit]
    # prefer to end at the last clause/sentence boundary within the window
    boundary = max(cut.rfind("."), cut.rfind("。"), cut.rfind(", "),
                   cut.rfind(" "))
    if boundary >= limit // 2:
        cut = cut[:boundary]
    return cut.rstrip(" ,·-") + "…"

CATEGORY_LABELS = {
    "safety": "안전·교통",
    "welfare": "복지·생활",
    "economy": "산업·예산",
    "agri_marine": "농수산·해양",
    "culture": "문화·관광",
    "general": "지역 이슈",
}


def summarize(item: dict) -> list[str]:
    first = _lead_sentence(item.get("body", ""))
    category = item.get("category")
    context_by_category = {
        "safety": "주요 위험 구간을 먼저 확인하고 현장 보완 순서를 정합니다.",
        "welfare": "대상자와 신청 일정을 함께 안내해 참여 기회를 넓힙니다.",
        "economy": "사업 효과가 지역 예산과 일자리 흐름으로 이어질 수 있습니다.",
        "agri_marine": "현장 여건을 반영한 점검과 지원이 단계적으로 진행됩니다.",
        "culture": "방문객 이동 흐름과 주변 상권 동선에도 변화가 예상됩니다.",
    }
    followup_by_category = {
        "safety": "장마 전 사전 대응 속도가 관건입니다.",
        "welfare": "모집 이후 지원 절차를 확인해야 합니다.",
        "economy": "후속 예산과 집행 일정이 다음 변수입니다.",
        "agri_marine": "현장 적용 시점과 지원 범위가 중요합니다.",
        "culture": "관광 체감 효과는 운영 방식에 달려 있습니다.",
    }
    second = context_by_category.get(category, "후속 조치와 현장 반응을 함께 볼 필요가 있습니다.")
    third = followup_by_category.get(category, "다음 발표에서 세부 일정이 확인됩니다.")
    return [first, second, third]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--max-cards", type=int, default=12,
                        help="cap on region cards in one bundle")
    parser.add_argument("--min-score", type=int, default=0,
                        help="drop region cards below this score")
    args = parser.parse_args()

    scored = load_json(ROOT / "data" / "daily" / args.date / "scored.json")
    # scored is already sorted by score desc, so the first item per region wins
    by_region = {}
    for item in scored:
        by_region.setdefault(item["region"], item)

    specs = []
    ranked = sorted(
        by_region.items(),
        key=lambda region_item: (-region_item[1]["score"], region_item[0]),
    )
    primary_items = [(r, it) for r, it in ranked
                     if it["score"] >= args.min_score][:args.max_cards]
    for region, item in primary_items:
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
