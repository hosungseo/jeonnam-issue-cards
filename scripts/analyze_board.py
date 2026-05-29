#!/usr/bin/env python3
"""Heuristically infer list/title/url/date selectors for a board page.

Given a board URL, finds article detail links (view/idx/seq/nttId/...),
locates their repeating ancestor unit, and derives selectors for the title
link and a date element. Prints a config-ready entry candidate.

Run: python3 scripts/analyze_board.py <url> [region]
"""
from __future__ import annotations

import json
import re
import sys

from bs4 import BeautifulSoup

import http_client

DETAIL_RE = re.compile(r"(mode=view|view\.do|idx=|seq=|nttId|articleNo|bbsIdx|nttSn|/view/|boardView|act=view|list_no=|dataSid=|wr_id=|board/detail)")
DATE_RE = re.compile(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}")


def _css_path(node) -> str:
    """Build a short, stable-ish CSS selector for a tag (name + first class)."""
    name = node.name
    classes = node.get("class") or []
    return f"{name}.{classes[0]}" if classes else name


def _repeating_unit(link):
    """Walk up until we find an ancestor that looks like a repeated row."""
    node = link
    for _ in range(6):
        node = node.parent
        if node is None or node.name in ("body", "html"):
            break
        if node.name in ("li", "tr") or (node.get("class") and
                any(c in ("item", "list", "row", "bbs_li", "board_li")
                    for c in node.get("class"))):
            return node
    return link.parent


def analyze(url: str, region: str = "") -> dict:
    html = http_client.fetch(url, timeout=12)
    if not html:
        return {"url": url, "status": "fetch_failed"}
    soup = BeautifulSoup(html, "lxml")
    links = [a for a in soup.find_all("a", href=True) if DETAIL_RE.search(a["href"])]
    if len(links) < 3:
        return {"url": url, "status": "no_detail_links", "found": len(links)}

    sample = links[0]
    unit = _repeating_unit(sample)
    list_sel = _css_path(unit)
    # title link selector relative to unit
    title_link = unit.find("a", href=DETAIL_RE)
    title_sel = _css_path(title_link)
    # date element inside unit
    date_sel = None
    date_fmt = None
    for el in unit.find_all(True):
        txt = el.get_text(strip=True)
        if DATE_RE.fullmatch(txt) or (DATE_RE.search(txt) and len(txt) <= 12):
            date_sel = _css_path(el)
            sep = "-" if "-" in txt else ("." if "." in txt else "/")
            date_fmt = f"%Y{sep}%m{sep}%d"
            break

    # count how many units match this list selector
    unit_count = len(soup.select(list_sel))
    entry = {
        "region": region,
        "source_name": f"{region} 보도자료" if region else "보도자료",
        "url": url,
        "list_selector": list_sel,
        "item": {
            "title": title_sel,
            "url": f"{title_sel}@href",
            "date": date_sel,
            "date_format": date_fmt,
        },
        "source_type": "official_city" if region.endswith("시") else "official_county",
        "trust_tier": 1,
    }
    return {"url": url, "status": "ok", "unit_count": unit_count,
            "sample_title": title_link.get_text(strip=True)[:40],
            "sample_date_sel": date_sel, "entry": entry}


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: analyze_board.py <url> [region]", file=sys.stderr)
        sys.exit(2)
    url = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else ""
    result = analyze(url, region)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
