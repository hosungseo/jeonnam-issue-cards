"""HTML board source adapter (requests + BeautifulSoup, selector-driven).

Config shape (per board):
  {
    "region": "목포시",
    "url": "https://.../boardList",
    "list_selector": "table.bbs tbody tr",
    "item": {
      "title": "td.title a",
      "url": "td.title a@href",
      "date": "td.date",
      "date_format": "%Y.%m.%d"
    },
    "source_type": "official_city",
    "trust_tier": 1
  }

A selector may end with "@attr" to extract an attribute instead of text.
Relative URLs are resolved against the board url.
"""
from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

import http_client
from adapters.base import SourceAdapter, make_item


# Common Korean board badge/icon text that leaks into title selectors.
_TITLE_NOISE = ("새로운글", "새글", "인기글", "NEW", "Hot")


def _extract(node, selector: str) -> str:
    attr = None
    if "@" in selector:
        selector, attr = selector.rsplit("@", 1)
    target = node.select_one(selector) if selector else node
    if target is None:
        return ""
    if attr:
        return (target.get(attr) or "").strip()
    return target.get_text(strip=True)


def _clean_title(text: str) -> str:
    """Strip icon/badge text and collapse whitespace from a board title."""
    import re
    for noise in _TITLE_NOISE:
        text = text.replace(noise, " ")
    return re.sub(r"\s+", " ", text).strip()


def _normalize_date(raw: str, fmt: Optional[str]) -> Optional[str]:
    raw = (raw or "").strip()
    if not raw:
        return None
    if fmt:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # last resort: pull YYYY[-./]MM[-./]DD
    import re
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", raw)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


class HtmlBoardAdapter(SourceAdapter):
    source_method = "html_board"

    def __init__(self, board: dict, fetch_fn=None):
        self.board = board
        self.region = board.get("region")
        self.url = board["url"]
        self.list_selector = board["list_selector"]
        self.item_sel = board["item"]
        self.source_type = board.get("source_type", "official_city")
        self.trust_tier = int(board.get("trust_tier", 1))
        self.name = board.get("source_name", self.region or self.url)
        self.render = bool(board.get("render", False))
        self._fetch = fetch_fn or http_client.fetch

    def fetch(self, date: str) -> list[dict]:
        if self.render and http_client.fallback_fetch and self._fetch is http_client.fetch:
            # JS-rendered board: go straight to the crawl4ai renderer
            html = http_client.fallback_fetch(self.url)
        else:
            html = self._fetch(self.url)
        if not html:
            print(f"[html_board] no content {self.name}", file=sys.stderr)
            return []
        soup = BeautifulSoup(html, "lxml")
        items = []
        for row in soup.select(self.list_selector):
            title = _clean_title(_extract(row, self.item_sel["title"]))
            if not title:
                continue
            url = _extract(row, self.item_sel.get("url", ""))
            if url:
                url = urljoin(self.url, url)
            published = _normalize_date(
                _extract(row, self.item_sel.get("date") or ""),
                self.item_sel.get("date_format"),
            )
            items.append(make_item(
                title=title,
                body=_extract(row, self.item_sel.get("body", "")),
                url=url,
                published_at=published,
                source_name=self.name,
                source_type=self.source_type,
                source_method=self.source_method,
                trust_tier=self.trust_tier,
                region=self.region,  # official board: source == region
            ))
        return items
