# hermes-skill-human20-kanban

Public Hermes skill for creating structured Reel/Short cards in the Human 2.0 team Kanban.

## Current scope

Version `0.1.0` supports one board only:

- **ВИДЕО / МОНТАЖ** (live name: `Видео /Вертикальные ролики`)

The skill makes the agent collect the destination column, assignee, deadline, labels, and attachment choice before creating a card. Reel cards receive a seven-platform publication checklist.

## Install

Clone the repository so the skill keeps its templates, references, helper, and tests:

```bash
git clone https://github.com/web3blind/hermes-skill-human20-kanban.git
cp -R hermes-skill-human20-kanban ~/.hermes/skills/human20-kanban
```

## Authentication

Set `HUMAN20_KANBAN_API_KEY` in the runtime environment. Do not commit the token.

## Usage

```bash
python scripts/human20_kanban.py inspect
cp templates/reels-card.example.json /tmp/reels-card.json
# Replace the example due_date with a real date within the next three days.
python scripts/human20_kanban.py plan-reels --input /tmp/reels-card.json
python scripts/human20_kanban.py create-reels --input /path/to/request.json
python scripts/human20_kanban.py card CARD_PUBLIC_ID
```

`plan-reels` is read-only. `create-reels` creates the card, checklist, optional labels, and optional attachment, then reads the card back.

## Development

```bash
python -m unittest discover -s tests -v
python scripts/validate_skill.py
```

## Security

No credentials belong in this repository. The client redacts authorization data from errors and never prints the token.

## License

MIT
