# hermes-skill-human20-kanban

Public Hermes skill for creating verified cards in any Human 2.0 team Kanban board.

## Behavior

The agent first lists every live board and asks the user to choose one unless the request already identifies it unambiguously. It then refreshes the selected board and collects the column, assignee, deadline, labels, and attachment choice.

Reel/Short cards use the **ВИДЕО / МОНТАЖ** specialization: source-video URL, deadline within three days, cover option, and a seven-platform publication checklist.

## Install

```bash
git clone https://github.com/PotapKong/hermes-skill-human20-kanban.git
cp -R hermes-skill-human20-kanban ~/.hermes/skills/human20-kanban
```

## Authentication

Set `HUMAN20_KANBAN_API_KEY` in the runtime environment. Never commit the token.

## Usage

```bash
python scripts/human20_kanban.py inspect
python scripts/human20_kanban.py inspect-board --board "Marketing"
python scripts/human20_kanban.py plan-card --input /path/to/request.json
python scripts/human20_kanban.py create-card --input /path/to/request.json
python scripts/human20_kanban.py card CARD_PUBLIC_ID
```

## Development

```bash
python -m unittest discover -s tests -v
python scripts/validate_skill.py
```

## License

MIT
