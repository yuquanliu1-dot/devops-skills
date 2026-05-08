#!/usr/bin/env python3
"""
init_wiki.py — Scaffold a new LLM-managed wiki at the given path.

Idempotent: if the wiki already exists, missing pieces are added without
overwriting existing files. Safe to re-run.

Usage:
    python init_wiki.py --path /path/to/wiki-root --name "My Wiki" --topic "Brief topic"
    python init_wiki.py                          # uses cwd, prompts for name/topic if missing
    python init_wiki.py --path . --name "Foo"    # minimal flags

Layout produced:
    <root>/
    ├── CLAUDE.md          # schema, written from template (only if missing)
    ├── README.md          # human-facing overview (only if missing)
    ├── raw/.gitkeep
    └── wiki/
        ├── index.md       # only if missing
        ├── log.md         # only if missing, with one bootstrap entry
        ├── sources/.gitkeep
        ├── entities/.gitkeep
        ├── concepts/.gitkeep
        └── notes/.gitkeep
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


# Path to the skill's templates directory, resolved relative to this script.
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "assets" / "templates"


def render_template(template_path: Path, replacements: dict[str, str]) -> str:
    """Read a template and substitute {{KEY}} placeholders."""
    text = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def write_if_missing(path: Path, content: str, *, created: list[str], skipped: list[str]) -> None:
    """Write content to path only if path doesn't exist. Track action."""
    if path.exists():
        skipped.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(str(path))


def ensure_dir_with_gitkeep(path: Path, *, created: list[str], skipped: list[str]) -> None:
    """Create a directory and a .gitkeep inside if not present."""
    path.mkdir(parents=True, exist_ok=True)
    keepfile = path / ".gitkeep"
    if not keepfile.exists():
        keepfile.write_text("", encoding="utf-8")
        created.append(str(keepfile))
    else:
        skipped.append(str(keepfile))


def init_wiki(root: Path, name: str, topic: str) -> tuple[list[str], list[str]]:
    """Scaffold the wiki at root. Returns (created, skipped) path lists."""
    created: list[str] = []
    skipped: list[str] = []

    today = dt.date.today().isoformat()

    # Top-level dirs
    root.mkdir(parents=True, exist_ok=True)
    ensure_dir_with_gitkeep(root / "raw", created=created, skipped=skipped)

    wiki_dir = root / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("sources", "entities", "concepts", "notes", "reports"):
        ensure_dir_with_gitkeep(wiki_dir / sub, created=created, skipped=skipped)

    # CLAUDE.md (schema)
    claude_template = TEMPLATES_DIR / "wiki-CLAUDE.md.tmpl"
    if claude_template.exists():
        content = render_template(
            claude_template,
            {"WIKI_NAME": name, "TOPIC": topic},
        )
        write_if_missing(root / "CLAUDE.md", content, created=created, skipped=skipped)
    else:
        # Fallback minimal schema if template is missing.
        write_if_missing(
            root / "CLAUDE.md",
            f"# {name}\n\n## Purpose\n\n{topic}\n",
            created=created, skipped=skipped,
        )

    # README.md (human-facing)
    readme = (
        f"# {name}\n\n"
        f"{topic}\n\n"
        "This is an LLM-managed wiki. The LLM (Claude) owns `wiki/`. "
        "I curate sources in `raw/`. The schema is in `CLAUDE.md`.\n\n"
        "## Layout\n\n"
        "- `raw/` — source documents I've collected\n"
        "- `wiki/` — LLM-generated pages\n"
        "- `CLAUDE.md` — schema for the LLM\n"
    )
    write_if_missing(root / "README.md", readme, created=created, skipped=skipped)

    # index.md
    index_template = TEMPLATES_DIR / "index.md.tmpl"
    if index_template.exists():
        content = index_template.read_text(encoding="utf-8")
    else:
        content = "# Index\n\n## Sources\n\n## Entities\n\n## Concepts\n\n## Notes\n"
    write_if_missing(wiki_dir / "index.md", content, created=created, skipped=skipped)

    # log.md
    log_template = TEMPLATES_DIR / "log.md.tmpl"
    if log_template.exists():
        bootstrap_details = f"Topic: {topic}" if topic else ""
        content = render_template(
            log_template,
            {"TODAY": today, "BOOTSTRAP_DETAILS": bootstrap_details},
        )
    else:
        content = f"# Log\n\n## [{today}] bootstrap | Wiki initialized\nTopic: {topic}\n"
    write_if_missing(wiki_dir / "log.md", content, created=created, skipped=skipped)

    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new LLM-managed wiki (idempotent).",
    )
    parser.add_argument(
        "--path", default=".",
        help="Wiki root directory (default: current directory).",
    )
    parser.add_argument(
        "--name", default=None,
        help="Wiki name. Used in CLAUDE.md and README.md.",
    )
    parser.add_argument(
        "--topic", default=None,
        help="One-sentence description of the wiki's purpose.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-file output, just print summary.",
    )
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()

    name = args.name or root.name
    topic = args.topic or "<edit CLAUDE.md to describe this wiki>"

    created, skipped = init_wiki(root, name, topic)

    if not args.quiet:
        if created:
            print(f"Created {len(created)} files/directories:")
            for p in created:
                print(f"  + {p}")
        if skipped:
            print(f"Skipped {len(skipped)} (already exist):")
            for p in skipped:
                print(f"  · {p}")

    print(f"\nWiki ready at: {root}")
    if created:
        print("Next steps:")
        print("  1. Edit CLAUDE.md to refine the schema for your topic.")
        print("  2. Drop your first source into raw/.")
        print("  3. Ask Claude to ingest it.")
    else:
        print("Wiki was already fully scaffolded — no changes made.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
