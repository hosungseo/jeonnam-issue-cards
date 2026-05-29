#!/usr/bin/env python3
"""Robust board selector discovery.

Key idea: a real board is where MANY detail links cluster in repeated rows
with the SAME tag+class signature. GNB menus / widgets have at most a few
stray detail links and inconsistent signatures, so signature frequency
filters them out.

Renders via crawl4ai (handles JS boards) then derives list/title/url/date
selectors from the dominant row signature.

Usage: smart_discover.py <url> <region> [--static]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

import http_client

ROOT = Path(__file__).resolve().parents[1]
DETAIL_RE = re.compile(
    r"(mode=view|view\.do|/view/|boardView|act=view|list_no=|nttId=|dataSid=|"
    r"wr_id=|seq=|idx=|articleNo|board/detail)")
DATE_RE = re.compile(r"\d{4}[.\-]\d{1,2}[.\-]\d{1,2}")
NOISE_HREF = re.compile(r"(survey|satisfaction|login|sitemap|#|javascript:)", re.I)


def _sig(node):
    return (node.name, tuple(node.get("class") or []))


def _row_of(link):
    node = link
    for _ in range(6):
        node = node.parent
        if node is None:
            return None
        if node.name in ("li", "tr"):
            return node
    return None


def _sel(node):
    cls = node.get("class") or []
    return f"{node.name}.{cls[0]}" if cls else node.name


def _rel_selector(row, target):
    """Selector for target relative to row: prefer tag.class, else tag."""
    cls = target.get("class") or []
    if cls:
        return f"{target.name}.{cls[0]}"
    # find a classed ancestor cell inside row
    cell = target.find_parent(["td", "span", "dd", "div"])
    if cell is not None and cell is not row and (cell.get("class")):
        return f"{cell.get('class')[0] and (cell.name + '.' + cell.get('class')[0])} {target.name}"
    return target.name


def discover(html: str, region: str):
    soup = BeautifulSoup(html, "lxml")
    details = [a for a in soup.find_all("a", href=True)
               if DETAIL_RE.search(a["href"]) and not NOISE_HREF.search(a["href"])]
    rows = [(_row_of(a), a) for a in details]
    rows = [(r, a) for r, a in rows if r is not None]

    # CMS-agnostic fallback: rows that carry a date AND a content link are
    # almost always board rows, regardless of the detail-href convention.
    if len({_sig(r) for r, _ in rows}) != 1 or len(rows) < 5:
        for el in soup.find_all(["li", "tr"]):
            txt = el.get_text(" ", strip=True)
            if not DATE_RE.search(txt):
                continue
            link = el.find("a", href=True)
            if link is None or NOISE_HREF.search(link.get("href", "")):
                continue
            rows.append((el, link))

    if len(rows) < 5:
        return {"status": "too_few_rows", "rows": len(rows)}

    # dominant row signature
    sig_counts = Counter(_sig(r) for r, _ in rows)
    best_sig, count = sig_counts.most_common(1)[0]
    if count < 5:
        return {"status": "no_dominant_signature", "top": count}

    sample_rows = [(r, a) for r, a in rows if _sig(r) == best_sig]
    sample_row, sample_link = sample_rows[0]

    # title link = longest-text detail link in the row
    cand = [a for a in sample_row.find_all("a", href=True)
            if DETAIL_RE.search(a["href"])]
    title_link = max(cand, key=lambda a: len(a.get_text(strip=True)), default=sample_link)
    title_sel = _sel(title_link)
    # if the link itself has no class, try its parent cell's class + 'a'
    if not (title_link.get("class")):
        cell = title_link.find_parent(["td", "span", "dd"])
        if cell is not None and cell.get("class"):
            title_sel = f"{cell.name}.{cell.get('class')[0]} a"

    # date element
    date_sel = None
    date_fmt = None
    for el in sample_row.find_all(["td", "span", "dd", "em", "p"]):
        t = el.get_text(strip=True)
        if DATE_RE.fullmatch(t) or (DATE_RE.search(t) and len(t) <= 12):
            if el.get("class"):
                date_sel = f"{el.name}.{el.get('class')[0]}"
            else:
                date_sel = el.name
            sep = "-" if "-" in t else ("." if "." in t else "/")
            date_fmt = f"%Y{sep}%m{sep}%d"
            break

    list_sel = best_sig[0] + ("." + best_sig[1][0] if best_sig[1] else "")
    item = {"title": title_sel, "url": (title_sel.split()[0] if " " in title_sel else title_sel) + "@href"
            if "@" not in title_sel else title_sel}
    # url: reuse title link selector
    item["url"] = (title_sel + "@href") if "a" == title_sel else (
        title_sel.replace(" a", " a") + "@href" if title_sel.endswith("a") else title_sel + "@href")
    if date_sel:
        item["date"] = date_sel
        item["date_format"] = date_fmt

    return {
        "status": "ok",
        "rows": count,
        "sample_title": title_link.get_text(strip=True)[:40],
        "sample_date": (date_sel, date_fmt),
        "list_selector": list_sel,
        "item": item,
    }


def render(url: str) -> str:
    venv = ROOT / ".venv-crawl" / "bin" / "python"
    cf = ROOT / "scripts" / "crawl_fetch.py"
    try:
        p = subprocess.run([str(venv), str(cf), url], capture_output=True,
                           text=True, timeout=80)
        return p.stdout if p.returncode == 0 else ""
    except Exception:
        return ""


def main():
    url = sys.argv[1]
    region = sys.argv[2]
    static = "--static" in sys.argv
    html = http_client.fetch(url, timeout=12) if static else ""
    used = "static"
    res = discover(html, region) if html else {"status": "no_static"}
    if res.get("status") != "ok":
        html = render(url)
        used = "render"
        res = discover(html, region) if html else {"status": "render_failed"}
    res["region"] = region
    res["url"] = url
    res["fetch"] = used
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
