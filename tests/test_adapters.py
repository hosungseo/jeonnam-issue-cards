import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import feedparser

from adapters.rss import RssAdapter
from adapters.html_board import HtmlBoardAdapter
from adapters.base import make_item
import collect

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class RssAdapterTests(unittest.TestCase):
    def test_parses_entries_and_normalizes_date(self):
        source = {"name": "샘플", "url": "x", "source_type": "official_city", "trust_tier": 1}
        adapter = RssAdapter(source, parse_fn=lambda url: feedparser.parse(str(FIXTURES / "sample_feed.xml")))
        items = adapter.fetch("2026-05-29")
        self.assertEqual(len(items), 2)
        first = items[0]
        self.assertEqual(first["title"], "여수시, 장마철 침수 취약도로 사전 점검 강화")
        self.assertEqual(first["published_at"], "2026-05-29")
        self.assertEqual(first["source_method"], "rss")
        self.assertEqual(first["source_type"], "official_city")

    def test_bad_feed_returns_empty(self):
        source = {"name": "bad", "url": "x", "source_type": "x", "trust_tier": 4}
        adapter = RssAdapter(source, parse_fn=lambda url: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertEqual(adapter.fetch("2026-05-29"), [])


class HtmlBoardAdapterTests(unittest.TestCase):
    def _adapter(self):
        html = (FIXTURES / "sample_board.html").read_text(encoding="utf-8")
        board = {
            "region": "목포시",
            "url": "https://www.mokpo.go.kr/press/list",
            "list_selector": "table.bbs tbody tr",
            "item": {"title": "td.title a", "url": "td.title a@href",
                     "date": "td.date", "date_format": "%Y.%m.%d"},
            "source_type": "official_city",
            "trust_tier": 1,
        }
        return HtmlBoardAdapter(board, fetch_fn=lambda url: html)

    def test_parses_rows_with_selectors(self):
        items = self._adapter().fetch("2026-05-29")
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["region"], "목포시")
        self.assertEqual(items[0]["published_at"], "2026-05-29")
        self.assertEqual(items[0]["source_method"], "html_board")

    def test_resolves_relative_and_absolute_urls(self):
        items = self._adapter().fetch("2026-05-29")
        self.assertEqual(items[0]["url"], "https://www.mokpo.go.kr/press/view?id=101")
        self.assertEqual(items[2]["url"], "https://www.mokpo.go.kr/press/view?id=103")

    def test_blocked_page_returns_empty(self):
        board = {"region": "목포시", "url": "x", "list_selector": "tr",
                 "item": {"title": "a"}, "source_type": "official_city", "trust_tier": 1}
        adapter = HtmlBoardAdapter(board, fetch_fn=lambda url: None)
        self.assertEqual(adapter.fetch("2026-05-29"), [])


class CollectTests(unittest.TestCase):
    def _fake_adapter(self, items, method="rss"):
        class Fake:
            source_method = method
            name = "fake"
            def fetch(self, date):
                return items
        return Fake()

    def test_fills_region_for_rss_and_keeps_board_region(self):
        rss_item = make_item(title="여수시 침수 점검", body="", url="https://a/1",
                             published_at="2026-05-29", source_name="rss", source_type="x",
                             source_method="rss", trust_tier=3)
        board_item = make_item(title="공원 정비", body="", url="https://b/2",
                               published_at="2026-05-29", source_name="목포시", source_type="official_city",
                               source_method="html_board", trust_tier=1, region="목포시")
        regions = ["여수시", "목포시"]
        items, counts = collect.collect("2026-05-29",
                                        adapters=[self._fake_adapter([rss_item, board_item])],
                                        regions=regions)
        by_url = {i["url"]: i for i in items}
        self.assertEqual(by_url["https://a/1"]["region"], "여수시")  # filled from text
        self.assertEqual(by_url["https://b/2"]["region"], "목포시")  # kept from board

    def test_dedupes_identical_urls(self):
        a = make_item(title="t1", body="", url="https://x.go.kr/p/1", published_at=None,
                      source_name="s", source_type="x", source_method="rss", trust_tier=3)
        b = make_item(title="t2", body="", url="https://www.x.go.kr/p/1/", published_at=None,
                      source_name="s", source_type="x", source_method="rss", trust_tier=3)
        items, _ = collect.collect("2026-05-29", adapters=[self._fake_adapter([a, b])], regions=[])
        self.assertEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
