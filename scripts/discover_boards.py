#!/usr/bin/env python3
"""Discover press-release board URLs/selectors for Jeonnam city/county sites.

Many Korean local-government sites share a standard CMS. This probes each
site's homepage for a press-release link, fetches the board, and checks
whether the Mokpo-style pattern (div.item > a.item_cont, dd.date) applies.
Outputs config-ready board entries and flags sites that need manual review.

Run:  python3 scripts/discover_boards.py [--write]
  --write merges discovered boards into config/sources.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup

import http_client
from common import ROOT, load_json

# 22 Jeonnam cities/counties -> official domain slug
CITY_SLUGS = {
    "목포시": "mokpo", "여수시": "yeosu", "순천시": "suncheon", "나주시": "naju",
    "광양시": "gwangyang", "담양군": "damyang", "곡성군": "gokseong",
    "구례군": "gurye", "고흥군": "goheung", "보성군": "boseong",
    "화순군": "hwasun", "장흥군": "jangheung", "강진군": "gangjin",
    "해남군": "haenam", "영암군": "yeongam", "무안군": "muan",
    "함평군": "hampyeong", "영광군": "yeonggwang", "장성군": "jangseong",
    "완도군": "wando", "진도군": "jindo", "신안군": "shinan",
}

PRESS_KEYWORDS = ("보도자료", "보도/해명", "보도·해명", "언론보도", "보도 자료",
                  "새소식", "시정소식", "군정소식", "보도 ", "보도자료실")

MOKPO_PATTERN = {
    "list_selector": "div.item",
    "item": {
        "title": "div.title_box h3",
        "url": "a.item_cont@href",
        "body": "div.cont_box p",
        "date": "dd.date",
        "date_format": "%Y-%m-%d",
    },
}


def find_press_link(html: str, base: str):
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        if any(k in text for k in PRESS_KEYWORDS):
            return urljoin(base, a["href"]), text
    return None, None


def matches_mokpo(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    items = soup.select("div.item")
    hits = 0
    for it in items:
        if it.select_one("div.title_box h3") and it.select_one("a.item_cont"):
            hits += 1
    return hits


def probe(region: str, slug: str) -> dict:
    base = f"https://www.{slug}.go.kr"
    home = http_client.fetch(base, timeout=12)
    if not home:
        return {"region": region, "status": "blocked_or_down", "base": base}
    press_url, label = find_press_link(home, base)
    if not press_url:
        return {"region": region, "status": "no_press_link", "base": base}
    board = http_client.fetch(press_url, timeout=12)
    if not board:
        return {"region": region, "status": "board_blocked", "url": press_url}
    hits = matches_mokpo(board)
    if hits >= 3:
        entry = {
            "region": region,
            "source_name": f"{region} 보도자료",
            "url": press_url,
            **MOKPO_PATTERN,
            "source_type": "official_city" if region.endswith("시") else "official_county",
            "trust_tier": 1,
        }
        return {"region": region, "status": "ok_mokpo", "items": hits, "entry": entry}

    # fall back to generic structure inference
    from analyze_board import analyze
    inferred = analyze(press_url, region)
    if inferred.get("status") == "ok" and inferred.get("unit_count", 0) >= 5:
        return {"region": region, "status": "ok_inferred",
                "items": inferred["unit_count"],
                "sample_title": inferred.get("sample_title"),
                "entry": inferred["entry"]}
    return {"region": region, "status": "unknown_structure", "url": press_url}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--only", help="comma-separated region subset")
    args = parser.parse_args()

    targets = CITY_SLUGS
    if args.only:
        wanted = set(args.only.split(","))
        targets = {k: v for k, v in CITY_SLUGS.items() if k in wanted}

    results = []
    discovered = []
    for region, slug in targets.items():
        r = probe(region, slug)
        results.append(r)
        status = r["status"]
        extra = f" items={r.get('items')} title={r.get('sample_title','')[:24]}" if status.startswith("ok") else ""
        print(f"{region:5} {status}{extra}  {r.get('url', r.get('base',''))}", file=sys.stderr)
        if status.startswith("ok"):
            discovered.append(r["entry"])

    ok = sum(1 for r in results if r["status"].startswith("ok"))
    print(f"\n[summary] ok={ok}/{len(results)}", file=sys.stderr)

    if args.write and discovered:
        cfg_path = ROOT / "config" / "sources.json"
        cfg = load_json(cfg_path) if cfg_path.exists() else {"html_boards": []}
        by_region = {b["region"]: b for b in cfg.get("html_boards", [])}
        for entry in discovered:
            by_region[entry["region"]] = entry  # discovered overrides
        cfg["html_boards"] = sorted(by_region.values(), key=lambda b: b["region"])
        with cfg_path.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"[write] merged {len(discovered)} boards -> {cfg_path}", file=sys.stderr)

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
