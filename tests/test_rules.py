import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "human20_kanban.py"
spec = importlib.util.spec_from_file_location("human20_kanban", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class RulesTest(unittest.TestCase):
    def base(self):
        return {
            "title": "Тестовый рилс",
            "video_url": "https://example.com/video",
            "description": "Контекст",
            "assignee": "Михаил",
            "due_date": "2026-07-18",
            "column": "Монтаж",
            "labels": ["Reels"],
            "new_label": None,
            "attachment_path": None,
        }

    def board(self):
        return {
            "name": "Видео /Вертикальные ролики",
            "publicId": mod.BOARD_PUBLIC_ID,
            "allLists": [{"name": "Монтаж", "publicId": "6g8bsvtm9yjl"}],
            "workspace": {"members": [{
                "publicId": "pfww09rr2cqx",
                "status": "active",
                "user": {"name": "Михаил"},
            }]},
            "labels": [{"name": "Reels", "publicId": "ikmbw72j8v5v"}],
        }

    def test_three_day_deadline_is_allowed(self):
        data = mod.validate_request(self.base(), today=date(2026, 7, 15))
        self.assertEqual(data["due_date"], "2026-07-18")

    def test_four_day_deadline_is_rejected(self):
        data = self.base()
        data["due_date"] = "2026-07-19"
        with self.assertRaisesRegex(ValueError, "three calendar days"):
            mod.validate_request(data, today=date(2026, 7, 15))

    def test_missing_required_fields_are_reported_together(self):
        data = self.base()
        data["assignee"] = ""
        data["column"] = ""
        with self.assertRaisesRegex(ValueError, "assignee, column"):
            mod.validate_request(data, today=date(2026, 7, 15))

    def test_checklist_contract(self):
        self.assertEqual(mod.SOCIAL_NETWORKS, [
            "Instagram", "YouTube", "ВК Видео", "Дзен", "RuTube", "TikTok", "Likee"
        ])

    def test_plan_resolves_live_names_to_ids(self):
        data = mod.validate_request(self.base(), today=date(2026, 7, 15))
        plan = mod.resolve_plan(data, self.board())
        self.assertEqual(plan["list"]["publicId"], "6g8bsvtm9yjl")
        self.assertEqual(plan["member"]["publicId"], "pfww09rr2cqx")
        self.assertEqual(plan["labels"][0]["publicId"], "ikmbw72j8v5v")
        self.assertEqual(plan["checklist"]["items"], mod.SOCIAL_NETWORKS)

    def test_attachment_must_exist(self):
        data = self.base()
        data["attachment_path"] = "/definitely/missing/cover.png"
        with self.assertRaisesRegex(ValueError, "not a file"):
            mod.validate_request(data, today=date(2026, 7, 15))

    def test_existing_attachment_is_allowed(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as handle:
            data = self.base()
            data["attachment_path"] = handle.name
            checked = mod.validate_request(data, today=date(2026, 7, 15))
            self.assertEqual(checked["attachment_path"], handle.name)


if __name__ == "__main__":
    unittest.main()
