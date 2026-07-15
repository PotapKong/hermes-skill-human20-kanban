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
            "board": "ВИДЕО / МОНТАЖ",
            "card_type": "reels",
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

    def board(self, board_id=None, name="Видео /Вертикальные ролики"):
        return {
            "name": name,
            "publicId": board_id or mod.VIDEO_BOARD_PUBLIC_ID,
            "allLists": [
                {"name": "Монтаж", "publicId": "6g8bsvtm9yjl"},
                {"name": "Передал для подготовки к публикации", "publicId": "553b64bb64c6"},
            ],
            "workspace": {"members": [{
                "publicId": "pfww09rr2cqx",
                "status": "active",
                "user": {"name": "Михаил"},
            }]},
            "labels": [{"name": "Reels", "publicId": "ikmbw72j8v5v"}],
        }

    def test_board_is_required(self):
        data = self.base()
        data["board"] = ""
        with self.assertRaisesRegex(ValueError, "board"):
            mod.validate_request(data, today=date(2026, 7, 15))

    def test_video_alias_resolves_to_live_board(self):
        boards = [{"name": "Видео /Вертикальные ролики", "publicId": mod.VIDEO_BOARD_PUBLIC_ID}]
        selected = mod.resolve_board(boards, "ВИДЕО / МОНТАЖ")
        self.assertEqual(selected["publicId"], mod.VIDEO_BOARD_PUBLIC_ID)

    def test_any_board_can_be_resolved_by_name(self):
        boards = [
            {"name": "Marketing", "publicId": "4lbjrmbvdm15"},
            {"name": "Human20 Lessons", "publicId": "0f79j6q2gqy8"},
        ]
        selected = mod.resolve_board(boards, "Human20 Lessons")
        self.assertEqual(selected["publicId"], "0f79j6q2gqy8")

    def test_duplicate_board_name_can_be_resolved_by_public_id(self):
        boards = [
            {"name": "Marketing", "publicId": "wjjtf11urlhf"},
            {"name": "Marketing", "publicId": "4lbjrmbvdm15"},
        ]
        selected = mod.resolve_board(boards, "4lbjrmbvdm15")
        self.assertEqual(selected["publicId"], "4lbjrmbvdm15")

    def test_active_boards_endpoint_has_no_archived_query(self):
        client = mod.KanClient(token="test-token")
        calls = []
        client.request = lambda method, path, payload=None: calls.append((method, path)) or []
        client.boards()
        self.assertEqual(calls, [("GET", f"/workspaces/{mod.WORKSPACE_PUBLIC_ID}/boards")])

    def test_three_day_reels_deadline_is_allowed(self):
        data = mod.validate_request(self.base(), today=date(2026, 7, 15))
        self.assertEqual(data["due_date"], "2026-07-18")

    def test_four_day_reels_deadline_is_rejected(self):
        data = self.base()
        data["due_date"] = "2026-07-19"
        with self.assertRaisesRegex(ValueError, "3 calendar days"):
            mod.validate_request(data, today=date(2026, 7, 15))

    def test_general_card_can_have_later_deadline(self):
        data = self.base()
        data.update({
            "board": "Human20 Lessons",
            "card_type": "general",
            "video_url": "",
            "due_date": "2026-08-01",
        })
        checked = mod.validate_request(data, today=date(2026, 7, 15))
        self.assertEqual(checked["due_date"], "2026-08-01")

    def test_reels_requires_video_url(self):
        data = self.base()
        data["video_url"] = ""
        with self.assertRaisesRegex(ValueError, "video_url"):
            mod.validate_request(data, today=date(2026, 7, 15))

    def test_reels_must_use_video_board(self):
        data = mod.validate_request(self.base(), today=date(2026, 7, 15))
        other = self.board(board_id="0f79j6q2gqy8", name="Human20 Lessons")
        with self.assertRaisesRegex(ValueError, "Reels cards must use"):
            mod.resolve_plan(data, other)

    def test_montage_card_has_no_publication_checklist(self):
        data = mod.validate_request(self.base(), today=date(2026, 7, 15))
        plan = mod.resolve_plan(data, self.board())
        self.assertIsNone(plan["checklist"])

    def test_mikhail_publication_card_has_publication_checklist(self):
        raw = self.base()
        raw["column"] = "Передал для подготовки к публикации"
        data = mod.validate_request(raw, today=date(2026, 7, 15))
        plan = mod.resolve_plan(data, self.board())
        self.assertEqual(plan["checklist"]["items"], mod.SOCIAL_NETWORKS)

    def test_publication_card_without_mikhail_has_no_checklist(self):
        raw = self.base()
        raw.update({"column": "Передал для подготовки к публикации", "assignee": "Лев"})
        data = mod.validate_request(raw, today=date(2026, 7, 15))
        board = self.board()
        board["workspace"]["members"].append({
            "publicId": "on6j1e0xtqqs",
            "status": "active",
            "user": {"name": "Лев"},
        })
        plan = mod.resolve_plan(data, board)
        self.assertIsNone(plan["checklist"])

    def test_explicit_publication_checklist_override(self):
        raw = self.base()
        raw["publication_checklist"] = True
        data = mod.validate_request(raw, today=date(2026, 7, 15))
        plan = mod.resolve_plan(data, self.board())
        self.assertEqual(plan["checklist"]["items"], mod.SOCIAL_NETWORKS)

    def test_multiple_assignees_are_resolved(self):
        data = self.base()
        data["assignee"] = "Михаил / Сергей SRG"
        checked = mod.validate_request(data, today=date(2026, 7, 15))
        board = self.board()
        board["workspace"]["members"].append({
            "publicId": "ky3ery3tu6e0",
            "status": "active",
            "user": {"name": "Сергей SRG"},
        })
        plan = mod.resolve_plan(checked, board)
        self.assertEqual([member["name"] for member in plan["members"]], ["Михаил", "Сергей SRG"])

    def test_general_plan_has_no_reels_checklist(self):
        data = self.base()
        data.update({"board": "Marketing", "card_type": "general", "video_url": ""})
        checked = mod.validate_request(data, today=date(2026, 7, 15))
        board = self.board(board_id="4lbjrmbvdm15", name="Marketing")
        plan = mod.resolve_plan(checked, board)
        self.assertIsNone(plan["checklist"])

    def test_checklist_contract(self):
        self.assertEqual(mod.SOCIAL_NETWORKS, [
            "Instagram", "YouTube", "ВК Видео", "Дзен", "RuTube", "TikTok", "Likee"
        ])

    def test_unique_names_removes_duplicate_board_columns(self):
        rows = [{"name": "В работе"}, {"name": "Монтаж"}, {"name": "В работе"}]
        self.assertEqual(mod.unique_names(rows), ["В работе", "Монтаж"])

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
