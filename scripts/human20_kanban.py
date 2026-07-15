#!/usr/bin/env python3
"""Human 2.0 Kanban helper for verified team card creation."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

BASE_URL = "https://team.20.business/api/v1"
WORKSPACE_PUBLIC_ID = "295v3oe7lbi4"
VIDEO_BOARD_PUBLIC_ID = "2ea096l0a4e3"
VIDEO_BOARD_ALIAS = "ВИДЕО / МОНТАЖ"
CHECKLIST_NAME = "Публикация Shorts/Reels"
SOCIAL_NETWORKS = [
    "Instagram",
    "YouTube",
    "ВК Видео",
    "Дзен",
    "RuTube",
    "TikTok",
    "Likee",
]


class KanError(RuntimeError):
    pass


def parse_due_date(value: str) -> date:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("due_date is required")
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise ValueError("due_date must start with YYYY-MM-DD") from exc


def validate_due_date(value: str, today: date | None = None, max_days: int | None = None) -> date:
    due = parse_due_date(value)
    current = today or datetime.now(timezone.utc).date()
    delta = (due - current).days
    if delta < 0:
        raise ValueError("due_date cannot be in the past")
    if max_days is not None and delta > max_days:
        raise ValueError(f"due_date must be no later than {max_days} calendar days from creation")
    return due


def is_reels(data: dict[str, Any]) -> bool:
    return str(data.get("card_type") or "").strip().casefold() in {"reels", "reel", "shorts", "short"}


def validate_request(data: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    required = ("board", "title", "assignee", "due_date", "column")
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if is_reels(data) and not str(data.get("video_url", "")).strip():
        missing.append("video_url")
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))

    video_url = str(data.get("video_url") or "").strip()
    if video_url and not video_url.startswith(("https://", "http://")):
        raise ValueError("video_url must be an http(s) URL")

    due = validate_due_date(str(data["due_date"]), today=today, max_days=3 if is_reels(data) else None)
    labels = data.get("labels") or []
    if not isinstance(labels, list) or any(not isinstance(x, str) or not x.strip() for x in labels):
        raise ValueError("labels must be a list of non-empty names")

    new_label = data.get("new_label")
    if new_label is not None:
        if not isinstance(new_label, dict) or not str(new_label.get("name", "")).strip():
            raise ValueError("new_label must contain name")
        colour = str(new_label.get("colour", "")).strip()
        if len(colour) != 7 or not colour.startswith("#"):
            raise ValueError("new_label.colour must be a #RRGGBB value")
        try:
            int(colour[1:], 16)
        except ValueError as exc:
            raise ValueError("new_label.colour must be a #RRGGBB value") from exc

    attachment = data.get("attachment_path")
    if attachment:
        path = Path(str(attachment)).expanduser()
        if not path.is_file():
            raise ValueError(f"attachment_path is not a file: {path}")

    return {
        **data,
        "board": str(data["board"]).strip(),
        "title": str(data["title"]).strip(),
        "video_url": video_url,
        "assignee": str(data["assignee"]).strip(),
        "column": str(data["column"]).strip(),
        "due_date": due.isoformat(),
        "labels": [x.strip() for x in labels],
        "card_type": "reels" if is_reels(data) else "general",
    }


def _pick_exact(items: list[dict[str, Any]], field: str, wanted: str, kind: str) -> dict[str, Any]:
    exact = [item for item in items if str(item.get(field, "")).casefold() == wanted.casefold()]
    if len(exact) == 1:
        return exact[0]
    partial = [item for item in items if wanted.casefold() in str(item.get(field, "")).casefold()]
    if len(partial) == 1:
        return partial[0]
    choices = ", ".join(str(item.get(field)) for item in items)
    if not exact and not partial:
        raise ValueError(f"unknown {kind} '{wanted}'. Available: {choices}")
    raise ValueError(f"ambiguous {kind} '{wanted}'. Use an exact name")


def resolve_board(boards: list[dict[str, Any]], wanted: str) -> dict[str, Any]:
    by_id = [x for x in boards if str(x.get("publicId", "")).casefold() == wanted.casefold()]
    if len(by_id) == 1:
        return by_id[0]
    if wanted.casefold() == VIDEO_BOARD_ALIAS.casefold():
        matches = [x for x in boards if x.get("publicId") == VIDEO_BOARD_PUBLIC_ID]
        if len(matches) == 1:
            return matches[0]
    return _pick_exact(boards, "name", wanted, "board")


def resolve_plan(data: dict[str, Any], board: dict[str, Any]) -> dict[str, Any]:
    lists = board.get("allLists") or board.get("lists") or []
    selected_list = _pick_exact(lists, "name", data["column"], "column")

    members = board.get("workspace", {}).get("members", [])
    member_rows = []
    for member in members:
        row = dict(member)
        row["displayName"] = (member.get("user") or {}).get("name") or member.get("email") or ""
        member_rows.append(row)
    selected_member = _pick_exact(member_rows, "displayName", data["assignee"], "assignee")

    board_labels = board.get("labels", [])
    resolved_labels = [_pick_exact(board_labels, "name", name, "label") for name in data.get("labels", [])]
    reels = data["card_type"] == "reels"
    if reels and board.get("publicId") != VIDEO_BOARD_PUBLIC_ID:
        raise ValueError(f"Reels cards must use board '{VIDEO_BOARD_ALIAS}'")

    return {
        "board": {"name": board.get("name"), "publicId": board.get("publicId")},
        "list": {"name": selected_list["name"], "publicId": selected_list["publicId"]},
        "member": {"name": selected_member["displayName"], "publicId": selected_member["publicId"]},
        "labels": [{"name": x["name"], "publicId": x["publicId"]} for x in resolved_labels],
        "new_label": data.get("new_label"),
        "attachment_path": data.get("attachment_path"),
        "title": data["title"],
        "description": build_description(data),
        "due_date": data["due_date"],
        "card_type": data["card_type"],
        "checklist": {"name": CHECKLIST_NAME, "items": SOCIAL_NETWORKS} if reels else None,
    }


def build_description(data: dict[str, Any]) -> str:
    lines = []
    if data.get("video_url"):
        lines.append(f"Исходное видео: {data['video_url']}")
    extra = str(data.get("description") or "").strip()
    if extra:
        if lines:
            lines.append("")
        lines.append(extra)
    return "\n".join(lines)


class KanClient:
    def __init__(self, token: str | None = None, base_url: str = BASE_URL):
        self.token = token or os.getenv("HUMAN20_KANBAN_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        if not self.token:
            raise KanError("HUMAN20_KANBAN_API_KEY is not set")

    def request(self, method: str, path: str, payload: Any = None) -> Any:
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = response.read()
                return json.loads(raw) if raw else {"status": response.status}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")[:1000]
            raise KanError(f"Kan API HTTP {exc.code}: {raw}") from exc
        except urllib.error.URLError as exc:
            raise KanError(f"Kan API connection failed: {exc.reason}") from exc

    def boards(self) -> list[dict[str, Any]]:
        # Kan API quirk: adding archived=false currently returns archived boards.
        # The endpoint without this query returns the active boards.
        return self.request("GET", f"/workspaces/{WORKSPACE_PUBLIC_ID}/boards")

    def board(self, board_id: str) -> dict[str, Any]:
        return self.request("GET", f"/boards/{board_id}")

    def card(self, card_id: str) -> dict[str, Any]:
        return self.request("GET", f"/cards/{card_id}")

    def create_label(self, board_id: str, name: str, colour: str) -> dict[str, Any]:
        return self.request("POST", "/labels", {
            "name": name,
            "boardPublicId": board_id,
            "colourCode": colour,
        })

    def create_card(self, plan: dict[str, Any], label_ids: list[str]) -> dict[str, Any]:
        return self.request("POST", "/cards", {
            "title": plan["title"],
            "description": plan["description"],
            "listPublicId": plan["list"]["publicId"],
            "labelPublicIds": label_ids,
            "memberPublicIds": [plan["member"]["publicId"]],
            "position": "end",
            "dueDate": plan["due_date"],
        })

    def create_checklist(self, card_id: str) -> dict[str, Any]:
        checklist = self.request("POST", f"/cards/{card_id}/checklists", {"name": CHECKLIST_NAME})
        checklist_id = checklist["publicId"]
        items = [self.request("POST", f"/checklists/{checklist_id}/items", {"title": title}) for title in SOCIAL_NETWORKS]
        return {"publicId": checklist_id, "items": items}

    def upload_attachment(self, card_id: str, file_path: str) -> dict[str, Any]:
        path = Path(file_path).expanduser().resolve()
        content = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        upload = self.request("POST", f"/cards/{card_id}/attachments/upload-url", {
            "filename": path.name,
            "contentType": content_type,
            "size": len(content),
        })
        put = urllib.request.Request(upload["url"], data=content, method="PUT", headers={"Content-Type": content_type})
        try:
            with urllib.request.urlopen(put, timeout=120) as response:
                if response.status not in (200, 201, 204):
                    raise KanError(f"attachment upload returned HTTP {response.status}")
        except urllib.error.URLError as exc:
            raise KanError(f"attachment upload failed: {exc.reason}") from exc
        return self.request("POST", f"/cards/{card_id}/attachments/confirm", {
            "s3Key": upload["key"],
            "filename": path.name,
            "originalFilename": path.name,
            "contentType": content_type,
            "size": len(content),
        })


def load_input(path: str) -> dict[str, Any]:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def public_card_url(card_id: str) -> str:
    return f"https://team.20.business/cards/{card_id}"


def unique_names(items: list[dict[str, Any]]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        name = str(item.get("name", "")).strip()
        key = name.casefold()
        if name and key not in seen:
            seen.add(key)
            result.append(name)
    return result


def inspect_command(client: KanClient) -> dict[str, Any]:
    boards = client.boards()
    return {
        "workspacePublicId": WORKSPACE_PUBLIC_ID,
        "boards": [
            {
                "name": board["name"],
                "publicId": board["publicId"],
                "columns": unique_names(board.get("lists", [])),
                "labels": unique_names(board.get("labels", [])),
                "alias": VIDEO_BOARD_ALIAS if board.get("publicId") == VIDEO_BOARD_PUBLIC_ID else None,
            }
            for board in boards
        ],
    }


def inspect_board_command(client: KanClient, wanted: str) -> dict[str, Any]:
    selected = resolve_board(client.boards(), wanted)
    board = client.board(selected["publicId"])
    return {
        "board": {"name": board.get("name"), "publicId": board.get("publicId")},
        "columns": [{"name": x["name"], "publicId": x["publicId"]} for x in board.get("allLists", [])],
        "members": [
            {"name": (x.get("user") or {}).get("name"), "publicId": x.get("publicId"), "status": x.get("status")}
            for x in board.get("workspace", {}).get("members", [])
            if x.get("status") == "active"
        ],
        "labels": [{"name": x["name"], "publicId": x["publicId"], "colour": x.get("colourCode")} for x in board.get("labels", [])],
    }


def build_plan(client: KanClient, raw: dict[str, Any]) -> dict[str, Any]:
    data = validate_request(raw)
    selected = resolve_board(client.boards(), data["board"])
    return resolve_plan(data, client.board(selected["publicId"]))


def create_card_flow(client: KanClient, raw: dict[str, Any]) -> dict[str, Any]:
    plan = build_plan(client, raw)
    label_ids = [x["publicId"] for x in plan["labels"]]
    created_label = None
    if plan.get("new_label"):
        created_label = client.create_label(
            plan["board"]["publicId"], plan["new_label"]["name"], plan["new_label"]["colour"]
        )
        label_ids.append(created_label["publicId"])

    card = client.create_card(plan, label_ids)
    card_id = card["publicId"]
    result: dict[str, Any] = {
        "status": "partial",
        "cardPublicId": card_id,
        "url": public_card_url(card_id),
        "createdLabel": created_label,
    }
    try:
        if plan.get("checklist"):
            result["checklist"] = client.create_checklist(card_id)
        if plan.get("attachment_path"):
            result["attachment"] = client.upload_attachment(card_id, plan["attachment_path"])
        result["readBack"] = client.card(card_id)
        result["status"] = "ok"
        return result
    except Exception as exc:
        result["error"] = str(exc)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect", help="List all live boards with columns and labels")
    board_parser = sub.add_parser("inspect-board", help="List columns, members, and labels for one board")
    board_parser.add_argument("--board", required=True)
    for command, help_text in (
        ("plan-card", "Validate and print a read-only card plan"),
        ("plan-reels", "Backward-compatible alias for plan-card"),
        ("create-card", "Create and verify a card"),
        ("create-reels", "Backward-compatible alias for create-card"),
    ):
        command_parser = sub.add_parser(command, help=help_text)
        command_parser.add_argument("--input", required=True)
    card_parser = sub.add_parser("card", help="Read a card back")
    card_parser.add_argument("card_id")
    args = parser.parse_args(argv)

    try:
        client = KanClient()
        if args.command == "inspect":
            result = inspect_command(client)
        elif args.command == "inspect-board":
            result = inspect_board_command(client, args.board)
        elif args.command in ("plan-card", "plan-reels"):
            result = build_plan(client, load_input(args.input))
        elif args.command in ("create-card", "create-reels"):
            result = create_card_flow(client, load_input(args.input))
        else:
            result = client.card(args.card_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") != "partial" else 2
    except (KanError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
