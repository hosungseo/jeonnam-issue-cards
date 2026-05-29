"""Build adapter instances from config and iterate them in policy order."""
from __future__ import annotations

from common import ROOT, load_json
from adapters.rss import RssAdapter
from adapters.html_board import HtmlBoardAdapter


def _load_optional(path):
    return load_json(path) if path.exists() else None


def build_adapters() -> list:
    """Return adapter instances ordered by crawler_strategy.default_order."""
    adapters = []

    rss_sources = _load_optional(ROOT / "config" / "news_rss_sources.json") or []
    for source in rss_sources:
        if source.get("url"):
            adapters.append(RssAdapter(source))

    # html boards: prefer config/sources.json, else allow html_boards key reuse
    sources_cfg = _load_optional(ROOT / "config" / "sources.json") or {}
    for board in sources_cfg.get("html_boards", []):
        if board.get("url") and board.get("list_selector"):
            adapters.append(HtmlBoardAdapter(board))

    order = {"rss": 0, "html_board": 1, "search_fallback": 2}
    adapters.sort(key=lambda a: order.get(a.source_method, 99))
    return adapters
