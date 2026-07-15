---
name: human20-kanban
version: 0.2.0
description: "Create Human 2.0 Kanban cards with verified routing."
author: Михаил + Hughie
license: MIT
metadata:
  hermes:
    tags: [human20, kanban, cards, tasks, reels, video]
    category: productivity
    created_by: agent
    requires_toolsets: [terminal]
---

# Human 2.0 Team Kanban

## When to use

Load this skill when the user asks to create, prepare, publish, or update a task/card in the Human 2.0 team Kanban at `https://team.20.business`. Natural triggers include combinations such as:

- «создай карточку Человек 2.0»;
- «поставь задачу команде Human 2.0»;
- «добавь в канбан Human20»;
- «создай карточку для рилса»;
- explicit `/human20-kanban`.

Do not wait for an exact phrase. Match the user's intent plus Human 2.0/team-Kanban context.

## Mandatory routing

Before creating any card:

1. Refresh all live boards with `inspect`.
2. If the user did not name an unambiguous board, show every available board and ask which one to use. When names repeat, include the public ID and columns so the user can distinguish them.
3. After board selection, refresh that board with `inspect-board`.
4. Ask for the destination column, assignee, deadline, labels, and attachment choice using live options.
5. Ask once for all missing fields. Preserve fields already supplied.

Never guess a board, column, assignee, label, deadline, or attachment requirement.

## Required card data

Resolve these fields before creation:

- board;
- title;
- useful description/context;
- destination column;
- assignee from the live member list;
- deadline;
- labels: existing, approved new label, or explicitly no labels;
- attachment: local file, generated asset, or explicitly no attachment.

Use `templates/card-request.md` when several fields are missing.

## Generic card contract

For every board:

- use the confirmed board and column;
- add at least one confirmed assignee;
- set the confirmed deadline;
- create a new label only after explicit approval of its name and colour;
- upload an attachment only when requested and verify it by reading the card back;
- place the card at the end of the chosen column unless the user asks otherwise.

## Reels specialization

A Reel/Short/vertical-video request uses `card_type: reels` and board **ВИДЕО / МОНТАЖ**. Ask for:

- Reel title;
- source-video URL from hosting or Telegram;
- assignee;
- deadline no later than three calendar days from creation;
- destination column;
- labels and whether a new label is needed;
- attachment choice, including an offer to generate and attach a cover.

Every Reels card receives checklist `Публикация Shorts/Reels` with exactly:

1. Instagram
2. YouTube
3. ВК Видео
4. Дзен
5. RuTube
6. TikTok
7. Likee

Generate a cover with an applicable cover/image skill or the configured image tool only after the user requests it. Verify the local file, upload it, then verify the attachment on the card.

## Procedure

1. List all boards:
   ```bash
   python scripts/human20_kanban.py inspect
   ```
   Use the endpoint without an `archived` query parameter. Kan currently returns archived boards when `?archived=false` is supplied.
2. Ask the user to choose a board if it was not explicit.
3. Read live details for the selected board:
   ```bash
   python scripts/human20_kanban.py inspect-board --board "BOARD NAME"
   ```
4. Collect missing data with `templates/card-request.md` or `templates/reels-card-request.md`.
5. Build JSON based on `templates/card.example.json`.
6. Validate without writing:
   ```bash
   python scripts/human20_kanban.py plan-card --input /path/to/request.json
   ```
7. Show the resolved plan when testing or when the request remains ambiguous.
8. Create:
   ```bash
   python scripts/human20_kanban.py create-card --input /path/to/request.json
   ```
9. Read back:
   ```bash
   python scripts/human20_kanban.py card CARD_PUBLIC_ID
   ```
10. Report board, column, title, assignee, deadline, labels, checklist, attachment, public ID, and URL.

## Authentication

The helper reads `HUMAN20_KANBAN_API_KEY`. Never put the token in prompts, repository files, command arguments, screenshots, logs, or generated documents.

## Safety

- Creating a fully specified card is allowed.
- Ask before creating a new label because it changes board taxonomy.
- Ask before deletion, archive, or moving an existing card.
- The helper intentionally exposes no delete/archive command.
- If the card is created but a checklist or attachment fails, report partial success with the card public ID. Never create a duplicate on retry.

## Verification

Completion requires a live card read-back confirming the selected board/list routing, title, assignee, deadline, labels, requested checklist, and requested attachments.
