import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from score import classify_category, score_item


class PipelineTests(unittest.TestCase):
    def test_personnel_notice_excluded(self):
        regions = ["광양시"]
        rules = {
            "source_scores": {"official_city": 5},
            "category_keywords": {"general": []},
            "exclude_keywords": ["인사발령"],
        }
        item = {
            "title": "광양시 인사발령 사항 알림",
            "body": "인사발령 사항입니다.",
            "url": "https://example.com/a",
            "source_type": "official_city",
        }
        self.assertIsNone(score_item(item, "2026-05-22", regions, rules))

    def test_title_category_has_priority(self):
        keyword_map = {
            "safety": ["안전"],
            "culture": ["관광"],
        }
        self.assertEqual(
            classify_category("목포시 관광 동선 개선", "보행 안전도 함께 점검", keyword_map),
            "culture",
        )


if __name__ == "__main__":
    unittest.main()

