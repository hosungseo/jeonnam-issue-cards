"""Source adapter interface and shared helpers."""
from __future__ import annotations

from typing import Optional


def make_item(*, title: str, body: str, url: str, published_at: Optional[str],
              source_name: str, source_type: str, source_method: str,
              trust_tier: int, region: Optional[str] = None) -> dict:
    """Build a normalized RawItem dict consumed by collect/score."""
    return {
        "title": (title or "").strip(),
        "body": (body or "").strip(),
        "url": (url or "").strip(),
        "published_at": published_at,
        "source_name": source_name,
        "source_type": source_type,
        "source_method": source_method,
        "trust_tier": trust_tier,
        "region": region,
    }


class SourceAdapter:
    """Base interface. Subclasses implement fetch()."""

    source_type: str = "unknown"
    source_method: str = "unknown"

    def fetch(self, date: str) -> list[dict]:
        raise NotImplementedError
