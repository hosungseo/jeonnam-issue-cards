"""RSS source adapter (feedparser-based)."""
from __future__ import annotations

import sys
import time
from typing import Optional

import feedparser

from adapters.base import SourceAdapter, make_item


def _entry_date(entry) -> Optional[str]:
    for key in ("published_parsed", "updated_parsed"):
        value = getattr(entry, key, None) or entry.get(key)
        if value:
            return time.strftime("%Y-%m-%d", value)
    return None


def _entry_body(entry) -> str:
    for key in ("summary", "description"):
        value = entry.get(key)
        if value:
            return value
    content = entry.get("content")
    if content and isinstance(content, list) and content:
        return content[0].get("value", "")
    return ""


class RssAdapter(SourceAdapter):
    source_method = "rss"

    def __init__(self, source: dict, parse_fn=feedparser.parse):
        self.source = source
        self.source_type = source.get("source_type", "unknown")
        self.trust_tier = int(source.get("trust_tier", 4))
        self.name = source.get("name", source.get("url", "rss"))
        self.url = source["url"]
        self._parse = parse_fn

    def fetch(self, date: str) -> list[dict]:
        try:
            feed = self._parse(self.url)
        except Exception as exc:  # noqa: BLE001 - one bad feed must not stop collect
            print(f"[rss] parse error {self.name}: {exc}", file=sys.stderr)
            return []
        items = []
        for entry in getattr(feed, "entries", []) or []:
            items.append(make_item(
                title=entry.get("title", ""),
                body=_entry_body(entry),
                url=entry.get("link", ""),
                published_at=_entry_date(entry),
                source_name=self.name,
                source_type=self.source_type,
                source_method=self.source_method,
                trust_tier=self.trust_tier,
            ))
        return items
