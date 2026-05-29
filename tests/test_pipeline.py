import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from score import classify_category, cluster_key, days_old, score_item


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

    def test_scoring_records_components_and_cluster_key(self):
        regions = ["여수시"]
        rules = {
            "source_scores": {"official_city": 5},
            "category_keywords": {"safety": ["침수"]},
            "exclude_keywords": [],
        }
        item = {
            "title": "여수시 침수 취약도로 점검 강화",
            "body": "침수 취약도로를 점검합니다.",
            "url": "https://example.com/a",
            "published_at": "2026-05-22",
            "source_type": "official_city",
        }
        scored = score_item(item, "2026-05-22", regions, rules)
        self.assertIsNotNone(scored)
        self.assertEqual(scored["days_old"], 0)
        self.assertEqual(scored["score_components"]["source"], 5)
        self.assertEqual(scored["score_components"]["freshness"], 3)
        self.assertTrue(scored["cluster_key"].startswith("여수시:safety:"))

    def test_days_old_handles_bad_dates(self):
        self.assertIsNone(days_old("bad-date", "2026-05-22"))
        self.assertEqual(days_old("2026-05-21", "2026-05-22"), 1)

    def test_cluster_key_is_stable_for_routine_verbs(self):
        self.assertEqual(
            cluster_key("목포시", "culture", "목포시 관광 동선 개선 사업 착수"),
            cluster_key("목포시", "culture", "목포시 관광 동선 사업 착수 개선"),
        )


if __name__ == "__main__":
    unittest.main()
