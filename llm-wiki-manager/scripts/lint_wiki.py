#!/usr/bin/env python3
"""
lint_wiki.py — Health check an LLM-managed wiki.

Catches mechanical issues only (broken links, orphan pages, index drift, stub
pages, log gaps). Semantic issues — stale claims, unflagged contradictions,
missing pages on cross-cutting entities — are out of scope; the LLM has to
spot those by reading.

By default writes a dated report to wiki/reports/lint-YYYY-MM-DD.md, then
auto-tracks it: adds an index entry under "Reports" and appends a log entry.
Re-running on the same day overwrites the day's report (idempotent daily).

Usage:
    python lint_wiki.py                              # default: wiki/reports/lint-<today>.md + auto-track
    python lint_wiki.py --path /path/to/wiki-root
    python lint_wiki.py --stdout                     # print to stdout, no file, no tracking
    python lint_wiki.py --report /tmp/lint.md        # custom path; auto-track only if inside wiki/
    python lint_wiki.py --no-track                   # write report file but skip index + log updates
    python lint_wiki.py --stub-words 30 --log-gap-days 60   # tune thresholds

Output is markdown, organized by severity (block, quality, suggestion).
Exit code 1 if any block-severity issue found.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


LINK_PATTERN = re.compile(
    r"\[(?P<text>[^\]]+)\]\((?P<url>[^)\s]+)(?:\s+\"[^\"]*\")?\)"
)
LOG_DATE_PATTERN = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\]")
INDEX_LINK_PATTERN = re.compile(
    r"^\s*-\s*\[([^\]]+)\]\(([^)]+)\)"
)


def is_external(url: str) -> bool:
    return url.startswith(("http://", "https://", "mailto:", "ftp://"))


def is_anchor_only(url: str) -> bool:
    return url.startswith("#")


def find_md_files(wiki_dir: Path) -> list[Path]:
    """All .md files under wiki/, excluding structural files and auto-generated reports.

    Skips:
      - wiki/index.md and wiki/log.md (structural, not content)
      - wiki/reports/* (auto-generated lint/audit artifacts; tracked separately)
    """
    skip_names = {"index.md", "log.md"}
    reports_dir = (wiki_dir / "reports").resolve()
    out: list[Path] = []
    for p in wiki_dir.rglob("*.md"):
        if p.name in skip_names:
            continue
        try:
            p.resolve().relative_to(reports_dir)
            continue  # path is inside reports/, skip
        except ValueError:
            pass
        out.append(p)
    return out


def collect_links(md_path: Path, wiki_dir: Path) -> list[tuple[str, Path]]:
    """
    Returns list of (raw_url, resolved_path_or_None) for all internal links in the file.
    Resolved path is None if the link is external or anchor-only.
    """
    text = md_path.read_text(encoding="utf-8", errors="replace")
    out: list[tuple[str, Path]] = []
    for m in LINK_PATTERN.finditer(text):
        url = m.group("url")
        if is_external(url) or is_anchor_only(url):
            continue
        # Strip URL fragment
        target = url.split("#", 1)[0]
        if not target:
            continue
        resolved = (md_path.parent / target).resolve()
        out.append((url, resolved))
    return out


def check_broken_links(
    md_files: list[Path], wiki_dir: Path, raw_dir: Path,
) -> tuple[list[dict], list[dict]]:
    """
    Two outputs:
      - broken: links pointing to non-existent files inside the wiki repo
      - raw_missing: links to raw/ files that don't exist
    """
    broken: list[dict] = []
    raw_missing: list[dict] = []
    for md in md_files:
        for url, resolved in collect_links(md, wiki_dir):
            if not resolved.exists():
                # Categorize: is the target inside raw/ ?
                try:
                    resolved.relative_to(raw_dir)
                    raw_missing.append({
                        "from": str(md),
                        "url": url,
                        "resolved": str(resolved),
                    })
                except ValueError:
                    broken.append({
                        "from": str(md),
                        "url": url,
                        "resolved": str(resolved),
                    })
    return broken, raw_missing


def check_orphans(md_files: list[Path], wiki_dir: Path, root: Path) -> list[Path]:
    """
    Pages with zero inbound links from any other page in wiki/ or from index.md.
    Returns list of orphan page paths.
    """
    # Build a set of resolved paths that ARE referenced by some page.
    referenced: set[Path] = set()
    index_md = wiki_dir / "index.md"

    candidate_files = list(md_files)
    if index_md.exists():
        candidate_files.append(index_md)

    for md in candidate_files:
        for _url, resolved in collect_links(md, wiki_dir):
            try:
                # Only count links targeting files that exist (otherwise they're broken,
                # not connections).
                if resolved.exists():
                    referenced.add(resolved)
            except OSError:
                continue

    orphans = [p for p in md_files if p.resolve() not in referenced]
    return orphans


def check_index_drift(
    md_files: list[Path], wiki_dir: Path,
) -> tuple[list[Path], list[dict]]:
    """
    Returns (pages_missing_from_index, dead_index_entries).
    """
    index_md = wiki_dir / "index.md"
    if not index_md.exists():
        return md_files, []

    text = index_md.read_text(encoding="utf-8", errors="replace")

    # Collect targets the index points to.
    indexed_targets: set[Path] = set()
    dead: list[dict] = []
    for line in text.splitlines():
        m = INDEX_LINK_PATTERN.match(line)
        if not m:
            continue
        title, url = m.group(1), m.group(2)
        if is_external(url) or is_anchor_only(url):
            continue
        target = (wiki_dir / url.split("#", 1)[0]).resolve()
        if target.exists():
            indexed_targets.add(target)
        else:
            dead.append({"title": title, "url": url, "resolved": str(target)})

    missing = [p for p in md_files if p.resolve() not in indexed_targets]
    return missing, dead


def check_stub_pages(md_files: list[Path], min_words: int) -> list[dict]:
    """Pages with fewer than min_words of body text (excluding frontmatter)."""
    stubs: list[dict] = []
    for md in md_files:
        text = md.read_text(encoding="utf-8", errors="replace")
        # Strip YAML frontmatter
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end != -1:
                text = text[end + 5:]
        words = len(text.split())
        if words < min_words:
            stubs.append({"path": str(md), "words": words})
    return stubs


def check_log_gaps(wiki_dir: Path, gap_days: int) -> list[dict]:
    """Look for stretches of >gap_days between log entries in log.md."""
    log_path = wiki_dir / "log.md"
    if not log_path.exists():
        return []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    dates: list[dt.date] = []
    for line in text.splitlines():
        m = LOG_DATE_PATTERN.match(line)
        if m:
            try:
                dates.append(dt.date.fromisoformat(m.group(1)))
            except ValueError:
                continue

    if len(dates) < 2:
        return []

    dates.sort()
    gaps: list[dict] = []
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i - 1]).days
        if delta > gap_days:
            gaps.append({
                "from": dates[i - 1].isoformat(),
                "to": dates[i].isoformat(),
                "days": delta,
            })
    return gaps


def check_slug_conventions(md_files: list[Path]) -> list[Path]:
    """Filenames that aren't lowercase-with-hyphens (excluding _-prefixed)."""
    bad: list[Path] = []
    pattern = re.compile(r"^[a-z0-9][a-z0-9\-]*\.md$")
    for md in md_files:
        name = md.name
        if name.startswith("_"):
            continue
        if not pattern.match(name):
            bad.append(md)
    return bad


def render_report(results: dict, root: Path, thresholds: dict) -> str:
    """Render the lint report as markdown."""
    today = dt.date.today().isoformat()
    lines: list[str] = []
    lines.append(f"# Lint report\n")
    lines.append(f"Wiki root: `{root}`")
    lines.append(f"Date: {today}\n")

    block_count = (
        len(results["broken_links"])
        + len(results["raw_missing"])
        + len(results["index_dead"])
    )
    quality_count = (
        len(results["orphans"])
        + len(results["index_missing"])
        + len(results["stubs"])
        + len(results["slug_mismatch"])
    )
    suggestion_count = len(results["log_gaps"])

    lines.append(
        f"Summary: **{block_count} block**, **{quality_count} quality**, "
        f"**{suggestion_count} suggestion**.\n"
    )

    # BLOCK
    lines.append("## Block (fix without asking)\n")
    if not block_count:
        lines.append("None. ✓\n")
    else:
        if results["broken_links"]:
            lines.append(f"### Broken links ({len(results['broken_links'])})\n")
            lines.append(
                "Markdown links pointing to files that don't exist inside the wiki.\n"
            )
            for entry in results["broken_links"]:
                lines.append(
                    f"- in `{entry['from']}`: `{entry['url']}` → `{entry['resolved']}`"
                )
            lines.append("")
        if results["raw_missing"]:
            lines.append(f"### Wiki citing missing `raw/` files ({len(results['raw_missing'])})\n")
            for entry in results["raw_missing"]:
                lines.append(
                    f"- in `{entry['from']}`: `{entry['url']}` → `{entry['resolved']}`"
                )
            lines.append("")
        if results["index_dead"]:
            lines.append(f"### Dead index entries ({len(results['index_dead'])})\n")
            lines.append("`wiki/index.md` references files that don't exist.\n")
            for entry in results["index_dead"]:
                lines.append(f"- [{entry['title']}]({entry['url']})")
            lines.append("")

    # QUALITY
    lines.append("## Quality (propose fixes, apply with approval)\n")
    if not quality_count:
        lines.append("None. ✓\n")
    else:
        if results["orphans"]:
            lines.append(f"### Orphan pages ({len(results['orphans'])})\n")
            lines.append("Pages with no inbound links from any other page or from the index.\n")
            for p in results["orphans"]:
                lines.append(f"- `{p}`")
            lines.append("")
        if results["index_missing"]:
            lines.append(f"### Pages missing from index ({len(results['index_missing'])})\n")
            for p in results["index_missing"]:
                lines.append(f"- `{p}`")
            lines.append("")
        if results["stubs"]:
            lines.append(
                f"### Stub pages — under {thresholds['stub_words']} words "
                f"({len(results['stubs'])})\n"
            )
            for s in results["stubs"]:
                lines.append(f"- `{s['path']}` ({s['words']} words)")
            lines.append("")
        if results["slug_mismatch"]:
            lines.append(f"### Slug convention mismatch ({len(results['slug_mismatch'])})\n")
            lines.append(
                "Filenames not matching `lowercase-with-hyphens.md`.\n"
            )
            for p in results["slug_mismatch"]:
                lines.append(f"- `{p}`")
            lines.append("")

    # SUGGESTIONS
    lines.append("## Suggestions (informational)\n")
    if not suggestion_count:
        lines.append("None. ✓\n")
    else:
        if results["log_gaps"]:
            lines.append(
                f"### Log gaps over {thresholds['log_gap_days']} days "
                f"({len(results['log_gaps'])})\n"
            )
            for g in results["log_gaps"]:
                lines.append(f"- {g['from']} → {g['to']} ({g['days']} days)")
            lines.append("")

    # Reminder of out-of-scope checks
    lines.append("---\n")
    lines.append("**Not checked here (LLM responsibility):** stale claims, ")
    lines.append("unflagged contradictions, missing pages on cross-cutting entities, ")
    lines.append("schema drift between `CLAUDE.md` and actual practice.\n")
    return "\n".join(lines)


def auto_track(
    report_path: Path,
    root: Path,
    block_total: int,
    quality_count: int,
    suggestion_count: int,
    today: str,
) -> None:
    """Update index.md and log.md to record this report.

    Best-effort: failures are reported but don't abort lint.
    Only called when report is being written inside wiki/reports/.
    """
    scripts_dir = Path(__file__).resolve().parent
    summary = (
        f"{block_total} block, {quality_count} quality, {suggestion_count} suggestion"
    )
    index_title = f"Lint {today}"
    log_title = "Health check"

    # Path relative to wiki/ for the index entry
    try:
        rel = report_path.resolve().relative_to((root / "wiki").resolve())
    except ValueError:
        return

    # update_index.py
    res = subprocess.run(
        [
            sys.executable, str(scripts_dir / "update_index.py"),
            "--path", str(root),
            "--category", "Reports",
            "--title", index_title,
            "--page-path", str(report_path),
            "--summary", summary,
        ],
        capture_output=True, text=True, check=False,
    )
    if res.returncode != 0:
        print(f"warning: update_index failed: {res.stderr.strip()}", file=sys.stderr)

    # append_log.py
    details = f"Wrote wiki/{rel.as_posix()}. {summary}."
    res = subprocess.run(
        [
            sys.executable, str(scripts_dir / "append_log.py"),
            "--path", str(root),
            "--action", "lint",
            "--title", log_title,
            "--details", details,
            "--date", today,
        ],
        capture_output=True, text=True, check=False,
    )
    if res.returncode != 0:
        print(f"warning: append_log failed: {res.stderr.strip()}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Health check an LLM-managed wiki.",
    )
    parser.add_argument(
        "--path", default=".",
        help="Wiki root directory (default: current directory).",
    )
    parser.add_argument(
        "--report", default=None,
        help="Custom report path. Default: wiki/reports/lint-<today>.md.",
    )
    parser.add_argument(
        "--stdout", action="store_true",
        help="Print report to stdout, do not write a file (no auto-track).",
    )
    parser.add_argument(
        "--no-track", action="store_true",
        help="Write the report file but skip the auto index/log updates.",
    )
    parser.add_argument(
        "--stub-words", type=int, default=50,
        help="Pages under this many body words are flagged as stubs (default: 50).",
    )
    parser.add_argument(
        "--log-gap-days", type=int, default=30,
        help="Log gaps longer than this many days are flagged (default: 30).",
    )
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    wiki_dir = root / "wiki"
    raw_dir = root / "raw"

    if not wiki_dir.exists():
        print(f"error: no wiki/ directory at {root}", file=sys.stderr)
        return 1

    today = dt.date.today().isoformat()

    md_files = find_md_files(wiki_dir)

    broken, raw_missing = check_broken_links(md_files, wiki_dir, raw_dir)
    orphans = check_orphans(md_files, wiki_dir, root)
    index_missing, index_dead = check_index_drift(md_files, wiki_dir)
    stubs = check_stub_pages(md_files, args.stub_words)
    log_gaps = check_log_gaps(wiki_dir, args.log_gap_days)
    slug_mismatch = check_slug_conventions(md_files)

    results = {
        "broken_links": broken,
        "raw_missing": raw_missing,
        "orphans": orphans,
        "index_missing": index_missing,
        "index_dead": index_dead,
        "stubs": stubs,
        "log_gaps": log_gaps,
        "slug_mismatch": slug_mismatch,
    }

    report = render_report(
        results, root,
        thresholds={"stub_words": args.stub_words, "log_gap_days": args.log_gap_days},
    )

    block_total = len(broken) + len(raw_missing) + len(index_dead)
    quality_count = (
        len(orphans) + len(index_missing) + len(stubs) + len(slug_mismatch)
    )
    suggestion_count = len(log_gaps)

    # Decide where the report goes.
    if args.stdout:
        print(report)
    else:
        if args.report:
            report_path = Path(args.report).expanduser().resolve()
        else:
            report_path = (wiki_dir / "reports" / f"lint-{today}.md").resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print(f"Report written to {report_path}")

        # Auto-track only when the report lives inside wiki/ — custom paths
        # outside the wiki are treated as one-off and not tracked.
        if not args.no_track:
            try:
                report_path.relative_to(wiki_dir.resolve())
            except ValueError:
                pass  # outside wiki/, skip tracking
            else:
                auto_track(
                    report_path, root,
                    block_total, quality_count, suggestion_count, today,
                )

    return 1 if block_total > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
