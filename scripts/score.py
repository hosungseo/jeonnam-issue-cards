#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime

from common import ROOT, infer_region, load_json, normalize_url, title_key, write_json


def classify_category(title: str, body: str, keyword_map: dict[str, list[str]]) -> str:
    best_category = "general"
    best_score = 0
    for category, keywords in keyword_map.items():
        category_score = 0
        for keyword in keywords:
            if keyword in title:
                category_score += 3
            if keyword in body:
                category_score += 1
        if category_score > best_score:
            best_category = category
            best_score = category_score
    return best_category


def days_old(published_at: str | None, run_date: str) -> int | None:
    if not published_at:
        return None
    try:
        published = datetime.strptime(published_at, "%Y-%m-%d").date()
        current = datetime.strptime(run_date, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (current - published).days


def cluster_key(region: str, category: str, title: str) -> str:
    tokens = title_key(title)
    for word in [region, "사업", "추진", "강화", "모집", "점검", "착수", "개선", "지원"]:
        tokens = tokens.replace(word.lower(), "")
    return f"{region}:{category}:{tokens[:18]}"


def score_item(item: dict, run_date: str, regions: list[str], rules: dict) -> dict | None:
    text = f"{item.get('title','')} {item.get('body','')}"
    if any(keyword in text for keyword in rules["exclude_keywords"]):
        return None

    region = item.get("region") or infer_region(text, regions)
    if region not in regions:
        return None

    components = {}
    components["source"] = rules["source_scores"].get(item.get("source_type"), 0)
    score = components["source"]
    if region in item.get("title", ""):
        components["region_in_title"] = 4
        score += components["region_in_title"]

    age = days_old(item.get("published_at"), run_date)
    if age == 0:
        components["freshness"] = 3
    elif age == 1:
        components["freshness"] = 1
    elif age is not None and age < 0:
        components["freshness"] = -2
    else:
        components["freshness"] = 0
    score += components["freshness"]

    category = classify_category(item.get("title", ""), item.get("body", ""), rules["category_keywords"])
    if category != "general":
        components["category_signal"] = 3
        score += components["category_signal"]

    return {
        **item,
        "region": region,
        "category": category,
        "score": score,
        "score_components": components,
        "days_old": age,
        "normalized_url": normalize_url(item["url"]),
        "title_key": title_key(item["title"]),
        "cluster_key": cluster_key(region, category, item["title"]),
        "confidence": "high" if score >= 10 else "medium",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    regions = load_json(ROOT / "config" / "regions.json")
    rules = load_json(ROOT / "config" / "scoring.json")
    items = load_json(ROOT / "data" / "raw" / f"{args.date}.json")

    seen = set()
    scored = []
    for item in items:
        candidate = score_item(item, args.date, regions, rules)
        if not candidate:
            continue
        key = (candidate["normalized_url"], candidate["title_key"])
        if key in seen:
            continue
        seen.add(key)
        scored.append(candidate)

    scored.sort(key=lambda x: x["score"], reverse=True)
    out = ROOT / "data" / "daily" / args.date / "scored.json"
    write_json(out, scored)
    print(f"scored {len(scored)} candidates -> {out}")


if __name__ == "__main__":
    main()
