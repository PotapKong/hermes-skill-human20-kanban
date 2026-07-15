---
name: human20-kanban
version: 0.1.0
description: "Create verified Human 2.0 Reels cards in the team Kanban."
author: Михаил + Hughie
license: MIT
metadata:
  hermes:
    tags: [human20, kanban, reels, video, tasks]
    category: productivity
    created_by: agent
    requires_toolsets: [terminal]
---

# Human 2.0 Team Kanban

## Scope

Use this skill when the user asks to create a task card for a Reel, Short, or vertical video in the Human 2.0 team Kanban at `https://team.20.business`.

Version `0.1.0` supports exactly one board:

- user-facing alias: **ВИДЕО / МОНТАЖ**;
- live board: **Видео /Вертикальные ролики**;
- board public ID: `jvyq1qdf0i1i`.

Do not route other Human 2.0 tasks with this version. Say that the requested board is outside the current scope and ask whether the skill should be extended.

## Required data before creation

Resolve every item before creating the card:

1. Reel title from the user's request.
2. Source-video URL: hosting URL or Telegram message URL.
3. Assignee from the live workspace member list.
4. Due date. It must be today through three calendar days from creation, inclusive.
5. Destination column on the supported board.
6. Labels:
   - ask whether to attach an existing label;
   - ask whether a new label is needed;
   - create a new label only after explicit approval of its name and colour.
7. Attachment:
   - ask whether a file must be attached;
   - for a Reel card, offer to generate and attach a cover;
   - never claim an attachment exists until the generated/local file is uploaded and read back from the card.

If several fields are missing, ask once using the compact template in `templates/reels-card-request.md`. Do not interrogate the user one field at a time. If the user already supplied a field, preserve it and ask only for missing or ambiguous data.

Always refresh columns, members, and labels from the live board before presenting options. IDs in `references/board.md` are fallbacks, not proof of current state.

## Card contract

Create the card only when all required choices are resolved.

- **Title:** the Reel title, concise and recognizable.
- **Description:** source-video URL plus useful context from the request. Do not invent a script, publication date, or production status.
- **Assignee:** at least one confirmed workspace member.
- **Due date:** no later than three calendar days from creation.
- **Column:** explicitly confirmed by the user.
- **Position:** end of the selected column unless the user asks otherwise.
- **Checklist name:** `Публикация Shorts/Reels`.
- **Checklist items, exactly in this order:**
  1. Instagram
  2. YouTube
  3. ВК Видео
  4. Дзен
  5. RuTube
  6. TikTok
  7. Likee
- **Cover:** generate and attach when requested/confirmed. Use an applicable cover/image skill if available; otherwise use the configured image-generation tool. Verify the local image before upload.

## Procedure

1. Confirm the request is a Reel/Short/vertical-video task for the supported board.
2. Run:
   ```bash
   python scripts/human20_kanban.py inspect
   ```
3. Collect missing data with the bundled request template.
4. Build a JSON payload based on `templates/reels-card.example.json`.
5. Validate without writing:
   ```bash
   python scripts/human20_kanban.py plan-reels --input /path/to/request.json
   ```
6. If a cover was requested, generate it and set `attachment_path` to the verified local file.
7. Create the card:
   ```bash
   python scripts/human20_kanban.py create-reels --input /path/to/request.json
   ```
8. Read the card back with the returned public ID:
   ```bash
   python scripts/human20_kanban.py card CARD_PUBLIC_ID
   ```
9. Report: card title, board, column, assignee, deadline, labels, checklist status, attachment status, public ID, and URL.

## Authentication

The helper reads the API token from `HUMAN20_KANBAN_API_KEY`. Never put the token in prompts, repository files, command arguments, screenshots, logs, or generated documents.

Example local setup, performed by the human/operator outside chat history:

```bash
export HUMAN20_KANBAN_API_KEY='...'
```

## Safety

- Creation is allowed after the card contract is complete.
- Ask before creating a new label because it changes board taxonomy.
- Ask before deletion or archiving.
- Never guess a member, column, label, deadline, or attachment requirement.
- Never silently move an existing card.
- If card creation succeeds but checklist or attachment creation fails, report partial success with the card public ID; do not create a duplicate card on retry.

## Verification

A task is complete only after a live read-back confirms:

- correct title and destination list;
- selected member attached;
- due date within the three-day rule;
- checklist exists with all seven networks;
- requested labels exist on the card;
- requested cover appears in attachments.
