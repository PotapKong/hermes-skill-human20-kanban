#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
required = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "scripts/human20_kanban.py",
    "templates/reels-card-request.md",
    "templates/reels-card.example.json",
    "references/board.md",
    "references/api.md",
]
errors = []
for rel in required:
    if not (ROOT / rel).is_file():
        errors.append(f"missing: {rel}")

skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
if not skill.startswith("---\n"):
    errors.append("SKILL.md must start with YAML frontmatter")
for field in ("name:", "description:", "version:"):
    if field not in skill.split("---", 2)[1]:
        errors.append(f"frontmatter missing {field}")
for network in ("Instagram", "YouTube", "ВК Видео", "Дзен", "RuTube", "TikTok", "Likee"):
    if network not in skill:
        errors.append(f"missing checklist network: {network}")

secret_pattern = re.compile(r"kan_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}")
for path in ROOT.rglob("*"):
    if path.is_file() and ".git" not in path.parts:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if secret_pattern.search(text):
            errors.append(f"credential-like secret found in {path.relative_to(ROOT)}")

if errors:
    print("FAIL")
    print("\n".join(f"- {x}" for x in errors))
    sys.exit(1)
print("OK: skill package structure, checklist contract, and secret scan passed")
