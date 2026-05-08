#!/usr/bin/env python3
"""
update_index.py — Add or update an entry in wiki/index.md under a given category.

Idempotent on (category, title): if an entry with the same title already exists
under the given category, it is replaced. Otherwise it is appended.

The index format:

    # Index
    ...
    ## Sources
    - [Title](sources/slug.md) — summary

    ## Entities
    - [Name](entities/slug.md) — summary

    ...

Usage:
    python update_index.py --category concepts \\
        --title "Nutritionism" \\
        --page-path "wiki/concepts/nutritionism.md" \\
        --summary "Reductive ideology that food = nutrients (5 sources)"

    python update_index.py --category sources \\
        --title "Pollan 2008 — In Defense of Food" \\
        --page-path "wiki/sources/pollan-2008-eat-food.md" \\
        --summary "book, foundational"

Notes:
- Category names are matched case-insensitively against existing top-level `## ` headings under `# Index`.
- If the category section doesn't exist yet, it's created in alphabetical order
  among the existing categories (after a configurable canonical order).
- The link path in the entry is computed as a path relative to wiki/, since
  index.md lives in wiki/.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# The canonical category order at the top of the index. Anything not listed
# here gets appended after these in the order it's first added.
CANONICAL_ORDER = ["Sources", "Entities", "Concepts", "Notes", "Reports"]


def find_index(root: Path) -> Path:
    index = root / "wiki" / "index.md"
    if not index.exists():
        raise FileNotFoundError(
            f"No index found at {index}. Run init_wiki.py first to scaffold the wiki."
        )
    return index


def normalize_category(category: str) -> str:
    """Title-case the category. 'concepts' -> 'Concepts'."""
    return category.strip().capitalize()


def relative_link_target(page_path: Path, wiki_dir: Path) -> str:
    """
    Compute the link target for an index entry.

    index.md lives in wiki/, so the link should be relative to wiki/.
    A page at wiki/concepts/foo.md is linked as concepts/foo.md.
    """
    page_path = Path(page_path)
    if page_path.is_absolute():
        try:
            rel = page_path.resolve().relative_to(wiki_dir.resolve())
        except ValueError as e:
            raise ValueError(
                f"page-path {page_path} is not inside wiki/ ({wiki_dir})"
            ) from e
        return rel.as_posix()
    # Relative path: handle two cases.
    # 1. "wiki/concepts/foo.md" — strip the wiki/ prefix.
    # 2. "concepts/foo.md" — already relative to wiki/.
    parts = page_path.parts
    if parts and parts[0] == "wiki":
        return Path(*parts[1:]).as_posix()
    return page_path.as_posix()


def parse_index(text: str) -> tuple[str, dict[str, list[str]]]:
    """
    Split index.md into (header_text, sections).

    header_text is everything before the first `## ` heading.
    sections is {category_name: [entry_lines]}, preserving order via dict insertion.
    """
    lines = text.splitlines()
    header_lines: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in lines:
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is None:
            header_lines.append(line)
        else:
            sections[current].append(line)

    header_text = "\n".join(header_lines).rstrip() + "\n\n" if header_lines else ""
    return header_text, sections


def render_index(header_text: str, sections: dict[str, list[str]]) -> str:
    """Reassemble the index, ordering categories by CANONICAL_ORDER then insertion."""
    ordered: list[str] = [c for c in CANONICAL_ORDER if c in sections]
    for cat in sections:
        if cat not in ordered:
            ordered.append(cat)

    parts = [header_text.rstrip() + "\n\n"] if header_text.strip() else []
    for cat in ordered:
        parts.append(f"## {cat}\n")
        body_lines = [ln for ln in sections[cat] if ln.strip() != ""]
        if body_lines:
            parts.append("\n".join(body_lines).rstrip() + "\n")
        parts.append("\n")
    return "".join(parts).rstrip() + "\n"


def upsert_entry(
    sections: dict[str, list[str]],
    category: str,
    title: str,
    link: str,
    summary: str,
) -> str:
    """
    Add or update an entry under the given category. Returns 'added' or 'updated'.

    Entry format: `- [Title](link) — summary`
    Match is on the (category, exact title) pair.
    """
    new_entry = f"- [{title}]({link}) — {summary}".rstrip(" —").rstrip()

    if category not in sections:
        sections[category] = [new_entry]
        return "added"

    # Find an existing line referencing the same title in markdown link.
    title_pattern = re.compile(
        r"^\s*-\s*\[" + re.escape(title) + r"\]\(",
    )
    existing = sections[category]
    for i, line in enumerate(existing):
        if title_pattern.match(line):
            existing[i] = new_entry
            return "updated"

    existing.append(new_entry)
    return "added"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add or update an entry in wiki/index.md under a category.",
    )
    parser.add_argument(
        "--path", default=".",
        help="Wiki root directory (default: current directory).",
    )
    parser.add_argument(
        "--category", required=True,
        help="Category name. Sources / Entities / Concepts / Notes — or any custom one.",
    )
    parser.add_argument(
        "--title", required=True,
        help="Page title. Used as the link text and as the upsert key.",
    )
    parser.add_argument(
        "--page-path", required=True,
        help="Path to the page being indexed. Either absolute, or relative to wiki root or to wiki/.",
    )
    parser.add_argument(
        "--summary", default="",
        help="One-line summary. Shown after the link with an em-dash.",
    )
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    wiki_dir = root / "wiki"

    try:
        index_path = find_index(root)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        link = relative_link_target(Path(args.page_path), wiki_dir)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    category = normalize_category(args.category)
    text = index_path.read_text(encoding="utf-8")
    header, sections = parse_index(text)
    action = upsert_entry(sections, category, args.title, link, args.summary)
    new_text = render_index(header, sections)
    index_path.write_text(new_text, encoding="utf-8")

    print(f"Index {action}: [{category}] {args.title} -> {link}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
