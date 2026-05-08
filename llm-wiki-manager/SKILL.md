---
name: llm-wiki-manager
description: Build, maintain, and query a personal LLM-managed wiki — a markdown knowledge base where the LLM owns all writing, cross-referencing, and bookkeeping while the user curates sources. Use this skill when the user wants to (1) bootstrap a new wiki, second brain, or research notebook; (2) ingest a new source (article, PDF, paper, transcript) and update relevant entity/concept pages, the index, and log; (3) query an existing wiki and synthesize an answer with citations, filing it back if useful; (4) update the wiki when a new source supersedes a claim across multiple pages (diff-before-write sweep); (5) lint the wiki for orphan pages, broken links, index drift, or stub pages — auto-dated reports; (6) learn or teach the pattern itself. Trigger this when the user mentions a "second brain", "research wiki", "knowledge base", or "Memex", or asks Claude to track sources across sessions. Bundles four idempotent scripts and enforces the bookkeeping discipline that makes wikis compound rather than rot.
license: MIT
metadata:
  author: sametbrr
  version: "1.1"
  tags:
    - wiki
    - knowledge-management
    - second-brain
    - research
    - karpathy
    - llm-wiki
---

# LLM Wiki Manager

A skill for running a personal LLM-managed wiki: a persistent, compounding markdown knowledge base where the human curates sources and asks questions, and the LLM does all the reading, writing, cross-referencing, and bookkeeping.

The pattern is intentionally tool-agnostic — it's just markdown files in a git repo. It works in any editor (Obsidian, VS Code, plain `vim`), and the skill makes no assumptions beyond "you have a filesystem and git". The user is on Claude Code.

## The three layers (memorize this)

Every wiki this skill manages has exactly three layers. Confusing them is the most common failure mode.

1. **`raw/`** — immutable sources the user curates. Articles, PDFs, transcripts, screenshots, data files. **The LLM reads from `raw/` but never modifies it.** This is the source of truth; if it gets edited the audit trail breaks.
2. **`wiki/`** — markdown pages the LLM owns entirely. Source summaries, entity pages, concept pages, comparisons, an `index.md`, a `log.md`. The user reads it; the LLM writes it. Pages link to each other and back to specific files in `raw/`.
3. **`CLAUDE.md`** (at the wiki root) — the schema. Tells future LLM sessions how this particular wiki is structured, what the page conventions are, how categories are named, how aggressive ingest should be. **Co-evolved with the user over time** — when something works, write it down here so the next session inherits it.

The whole point of the pattern is that `wiki/` is a **persistent, compounding artifact**. It is *not* re-derived on every query. New sources update existing pages in place. That is what separates this from RAG.

## Mode router

When this skill triggers, identify which mode applies and read the matching reference file. The user rarely names the mode explicitly — infer it from context. If genuinely ambiguous, ask one short clarifying question.

| Mode | Triggers | Reference |
|---|---|---|
| **Teach** | "how does this pattern work", "explain the LLM wiki idea", first-time user, no `CLAUDE.md` and no `wiki/` and they're asking how it works rather than to set one up | `references/teaching-mode.md` |
| **Bootstrap** | "set up a wiki", "start from scratch", "init a knowledge base", working directory has no `wiki/` yet and the user wants one | `references/bootstrap-workflow.md` |
| **Ingest** | new source dropped (file in `raw/`, pasted URL, attached PDF), "add this to the wiki", "file this", "I just read X" | `references/ingest-workflow.md` |
| **Query** | question against existing wiki content, "what do we know about X", "compare X and Y from my notes", "based on what I've collected…" | `references/query-workflow.md` |
| **Update** | "X is no longer right", "Smith 2024 supersedes Keys 1980", a new source invalidates a claim across **3+ existing pages** (not just one), user explicitly correcting a factual error they spotted | `references/update-workflow.md` |
| **Multi-wiki** | "add this to my global wiki", "file to obsidian", "what does the global wiki say about X", "check my notes on Y", "promote this page to global", "lint both wikis", any operation that explicitly targets a second wiki location, or project's `CLAUDE.md` declares an `## External Wiki` section | `references/multi-wiki-routing.md` |
| **Lint** | "health check", "audit the wiki", "find contradictions", "anything broken", periodic maintenance request | `references/lint-workflow.md` |
| **Schema-evolve** | "update CLAUDE.md", "we should always do X going forward", convention drift noticed during another mode | `references/schema-design-guide.md` |

If multiple modes apply (e.g., user asks a question and wants the answer filed back), do them in sequence and log each one.

**Update vs. Ingest's Disputes handling — important distinction.** Ingest already handles contradictions on a single page by adding a Disputes section. Switch to **Update mode** only when the new source's claim affects **multiple existing pages** — that is, when the same idea is paraphrased across the wiki and a single Disputes section won't keep the wiki internally consistent. If only one page is affected, stay in ingest. See `references/update-workflow.md` for the precise trigger checklist.

**Multi-wiki requires `CLAUDE.md` configuration.** Before any multi-wiki operation, read the project `CLAUDE.md` for an `## External Wiki` section that declares the global wiki path and routing rules. If the section is missing and a multi-wiki operation is requested, **run Schema-evolve first** to add it, then proceed. Never guess or assume the global wiki path. See `references/multi-wiki-routing.md` for the one-time setup block and the four canonical scenarios.

## Core invariants (apply in every mode)

These are the disciplines that make a wiki compound. Skipping them is how wikis rot.

### 1. The user owns `raw/`. The LLM owns `wiki/`.

Never write to `raw/`. Never ask the user to edit `wiki/` by hand (they can if they want, but the skill never asks). When summarizing a source, the summary lives in `wiki/sources/<source-slug>.md` and links back to the file in `raw/`.

### 2. Every operation logs to `log.md`.

After any ingest, query, update, or lint, append a single entry using `scripts/append_log.py`:

```
## [YYYY-MM-DD] ingest | <source title>
## [YYYY-MM-DD] query  | <one-line question>
## [YYYY-MM-DD] update | <claim corrected, source authority>
## [YYYY-MM-DD] lint   | <pages touched or "clean">
```

Consistent prefix matters — it makes the log greppable: `grep "^## \[" log.md | tail -20` shows recent activity. The script enforces the format. For lint, the script auto-logs by default — you don't need a separate `append_log.py` call after running `lint_wiki.py`. For ingest/query/update, the LLM calls the script.

### 3. Every new or significantly-updated page touches `index.md`.

Use `scripts/update_index.py`. The index is content-oriented: category, title, one-line summary, link. It is the LLM's primary navigation aid in future sessions when the wiki is large. Stale index = wiki that feels lost.

### 4. Cross-reference aggressively.

When ingesting a source about, say, a person who already has an entity page, **update that entity page** with the new information. Don't leave the connection implicit in the source summary. The whole value proposition is that connections are made eagerly, while context is fresh, not lazily at query time.

Use markdown wiki-style links: `[Page Title](../entities/page-title.md)` or, if the user prefers Obsidian-style, `[[page-title]]`. Pick one convention and record it in `CLAUDE.md`.

### 5. Cite back to `raw/`.

Every claim in a wiki page should be traceable to a specific source. The standard pattern in source-summary pages is:

```markdown
> Quote or paraphrase from the source.
> — `raw/2026-01-pollan-eat-food.pdf`, p. 14
```

In synthesis pages (entity, concept, comparison), use inline references like `(see [Pollan 2026](../sources/pollan-eat-food.md))`. The reader should always be able to trace a claim back to a real source.

### 6. Flag contradictions, don't silently overwrite.

If a new source contradicts an existing claim on a wiki page, do **not** just replace the old claim. Add the new claim alongside, mark both with their source, and note the conflict — usually as a `> [!warning] Sources disagree` callout or a "Disputes" subsection. The user decides which to believe; the wiki records the disagreement.

### 7. The schema lives in `CLAUDE.md` and is updated when conventions change.

If a working pattern emerges in conversation ("let's always tag book chapters with `chapter:N`"), write it into `CLAUDE.md` immediately so the next session inherits it. The user shouldn't have to re-explain conventions every session.

### 8. If the project's `CLAUDE.md` declares an `External Wiki`, honor it.

Some users run two wikis: a per-project wiki at the working directory and a long-lived global wiki (often an existing Obsidian vault) at a fixed path. The project's `CLAUDE.md` declares the global wiki's location with a section like:

```markdown
## External Wiki

Global knowledge base: ~/Documents/obsidian/
```

When this section is present, **read both `CLAUDE.md` files at session start** (project + global) so you know each wiki's schema. Route writes per the user's rules: project-specific knowledge to the project wiki, portable concepts to the global wiki. Always pass `--path` to scripts targeting the chosen wiki — never assume the current working directory is the right target. **Cross-wiki links must be absolute** (`~/...`), never relative across wiki boundaries. See `references/multi-wiki-routing.md` for the four canonical scenarios (write-to-global, pull-from-global, promote, dual-lint).

## Standard wiki layout

`init_wiki.py` produces:

```
<wiki-root>/
├── CLAUDE.md          # Schema for the wiki itself (instructions to future Claude)
├── README.md          # Human-facing overview (optional but useful)
├── raw/               # User-curated sources — LLM reads, never writes
│   └── .gitkeep
└── wiki/              # LLM-managed pages
    ├── index.md       # Content catalog by category
    ├── log.md         # Chronological log of operations
    ├── sources/       # One summary page per ingested source
    ├── entities/      # People, organizations, products, places
    ├── concepts/      # Ideas, theories, frameworks, terms
    ├── notes/         # Loose pages that don't fit elsewhere yet
    └── reports/       # Auto-generated dated lint/audit reports (scripts write here, not the LLM)
```

The `entities/`, `concepts/`, `sources/`, `notes/` split is the **default** suggestion. Many wikis converge on a different taxonomy as they grow (e.g. a research wiki might use `papers/`, `methods/`, `findings/`, `open-questions/`). When the natural taxonomy diverges, **update `CLAUDE.md` to reflect the new convention** and reorganize incrementally.

`reports/` is special: it's automated output, not user content. `lint_wiki.py` (and future audit tooling) writes dated files here — `lint-2026-05-07.md`, `audit-saturated-fat-2026-05-07.md` — and same-day re-runs overwrite (idempotent daily). Lint excludes this folder from orphan/stub/index-drift checks.

## Bundled scripts

All four are in `scripts/`. They are deliberately small, idempotent, and dependency-free (Python stdlib only).

- **`init_wiki.py`** — scaffold a new wiki at a given path. Idempotent. See `references/bootstrap-workflow.md`.
- **`append_log.py`** — append a log entry with the consistent `## [YYYY-MM-DD] action | title` prefix. Use after every ingest, query, update, and lint. See script `--help`. Valid actions: `ingest`, `query`, `update`, `lint`, `audit`, `bootstrap`, `schema-evolve`, `note`.
- **`update_index.py`** — add or update an entry under a category in `index.md`. Idempotent on (category, title) — won't duplicate.
- **`lint_wiki.py`** — scan for orphan pages, broken links, index/filesystem drift, log gaps. **Default behavior**: writes report to `wiki/reports/lint-<today>.md`, then auto-tracks (adds Reports index entry, appends `lint | Health check` log entry). Same-day re-runs overwrite the report file. Override with `--stdout` (no file, no track), `--report PATH` (custom path; auto-tracks only if path is inside `wiki/`), or `--no-track` (write file but skip index/log updates). See `references/lint-workflow.md`.

Always prefer running these scripts to hand-editing `index.md` or `log.md`. They keep the format consistent across sessions and make the wiki greppable.

For **update mode**, no new script is needed — the workflow uses `append_log.py` (with `--action update`) and `update_index.py` orchestrated by the LLM following `references/update-workflow.md`. The diffs and multi-page sweep are LLM work, not script work, because they require semantic judgment.

For **multi-wiki mode**, scripts are called with `--path <wiki-root>` to operate on the chosen wiki. The routing decision (which wiki receives the write) comes from the project `CLAUDE.md`'s `## External Wiki` section. Never rely on the current working directory — always pass `--path` explicitly. See `references/multi-wiki-routing.md`.

## Bundled templates

In `assets/templates/`. Use them as starting points; adapt freely:

- `wiki-CLAUDE.md.tmpl` — the schema file dropped into a fresh wiki by `init_wiki.py`
- `index.md.tmpl`, `log.md.tmpl` — initial scaffolding
- `source-summary.md.tmpl` — one ingested source, full structure
- `entity-page.md.tmpl` — a person, org, place, or product
- `concept-page.md.tmpl` — an idea, framework, or term
- `comparison-page.md.tmpl` — for "X vs Y" pages, often produced as query outputs

`assets/examples/healthy-wiki-tree.txt` shows what a mature wiki of ~50 sources looks like — useful when teaching the pattern or sanity-checking organization.

## When in doubt

Read `references/philosophy.md` for the why and `references/architecture.md` for the what. Both are short. The workflow files are the how: `bootstrap-workflow.md`, `ingest-workflow.md`, `query-workflow.md`, `update-workflow.md`, `multi-wiki-routing.md`, `lint-workflow.md`, `schema-design-guide.md`, `teaching-mode.md`.

The single most important principle: **the LLM does the bookkeeping.** Cross-references, index updates, log entries, contradiction-flagging, stale-claim review, multi-wiki routing. That work is what makes the wiki compound. Skipping it because "the user didn't ask" is the failure mode this skill exists to prevent.
