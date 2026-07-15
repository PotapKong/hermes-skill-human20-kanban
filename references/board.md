# Live routing rules

The API is the source of truth. Run `inspect` before asking for a board and `inspect-board` after the user chooses one.

- Workspace: `human20` (`295v3oe7lbi4`)
- Reels board alias: `ВИДЕО / МОНТАЖ`
- Reels live board: `ВИДЕО / МОНТАЖ`
- Reels board public ID: `2ea096l0a4e3`

Important API quirk verified on 2026-07-15: `GET /workspaces/{id}/boards`
returns active boards, while adding `?archived=false` incorrectly returns archived
boards. Do not add the query parameter until the API behavior is fixed and rechecked.

Board names, columns, labels, and members can change. Never present this snapshot as current without a live read.
