---
name: easy-docs
description: Organize and standardize repository documentation with a deterministic docs system and OKF (Open Knowledge Format) knowledge headers. Use when the user asks to set up or clean up docs structure, documentation rules, or a documentation index; create docs/index.md; add, generate, or validate YAML frontmatter headers on markdown docs; regenerate a docs catalog programmatically; fix a stale or drifted documentation index; check OKF knowledge-bundle conformance; or make docs agent-readable.
compatibility: Works with Claude Code, Cursor, Codex, and other Agent Skills clients. Needs Bash, Read, Write, Edit, Glob, Grep tools and write access to the target repository. The helper script requires `uv` (Python >= 3.11); `git` is optional and only improves timestamp derivation. Running this skill's own tests additionally requires `just`. No network access.
allowed-tools: Bash Read Write Edit Glob Grep
license: GPL-3.0-or-later
metadata:
  version: "0.1.0"
  argument-hint: "[target repo] [scaffold|headers|index|check]"
  author: Davi Mello <dsmello@ollem.io>
---

# Easy Docs

Create and maintain an agent-friendly documentation system: a predictable
`docs/` tree, OKF frontmatter headers on every doc, and programmatically
generated indexes that never drift from the filesystem.

This skill treats the repository's `docs/` tree as an **OKF knowledge
bundle**: every doc is a concept document with YAML frontmatter, and every
directory index is generated from those headers, not written by hand.

## Docs System Contract

These rules apply to every repository this skill touches:

- `docs/index.md` is the complete documentation table of contents.
- `AGENTS.md` links the docs entrypoints agents need first; `docs/index.md`
  carries the full hierarchy.
- Root `docs/*.md` files stay below 500 lines. When a topic outgrows that,
  split it into `docs/<topic>/index.md` plus supporting files.
- Every specialized docs folder (`decisions/`, `design/`, `exec-plans/`,
  `references/`, and any new topic folder) has an `index.md`.
- `docs/references/docs-maintenance.md` owns how indexes and `AGENTS.md` are
  kept current.
- Generated catalog regions are owned by the helper script. Never hand-edit
  content between generated markers; edit the source docs and regenerate.
- New placeholder files must be replaced with real content before the related
  workflow is considered complete.

## OKF Fundamentals

OKF (Open Knowledge Format, v0.1) represents knowledge as a directory tree of
markdown files with YAML frontmatter — readable by humans, parseable by
agents, diffable in git. Reference: the OKF SPEC in
GoogleCloudPlatform/knowledge-catalog (`okf/SPEC.md`).

Core terms:

- **Knowledge bundle** — a self-contained directory tree of concept
  documents. In this skill, the bundle root is `docs/` by default.
- **Concept document** — one markdown file describing one concept (a guide,
  a decision, a table, a playbook…). Frontmatter + body.
- **Concept ID** — the file's path inside the bundle without `.md`
  (`decisions/adr-0001.md` → `decisions/adr-0001`).
- **Reserved filenames** — `index.md` (directory listing, §6) and `log.md`
  (update history, §7) are structural, not concept documents. The names are
  exact and case-sensitive per OKF §3.1; an `INDEX.md` is an ordinary concept
  document.

### Frontmatter contract

Every non-reserved `.md` file in the bundle carries a frontmatter block:

```yaml
---
type: Guide            # REQUIRED — the only OKF-required key
title: Local Development
description: One-line summary used by index generators and search.
resource: https://…    # optional canonical URI of the described asset
tags: [dev, setup]     # optional cross-cutting categorization
timestamp: 2026-07-15  # last meaningful update (ISO 8601)
---
```

Rules that matter in practice:

- `type` is required and free-form; pick short, self-explanatory values.
  Consumers must tolerate unknown types, so do not invent a registry.
- `title` and `description` feed generated indexes — write them for the
  reader scanning a catalog, not for the file itself.
- Producer-defined extra keys are allowed; never strip keys you do not
  recognize.
- Bodies favor structural markdown (headings, tables, fenced code) over
  prose. Conventional headings: `# Schema`, `# Examples`, `# Citations`.

### Default type taxonomy

The helper derives `type` from the path when adding missing headers:

| Path inside bundle        | Default `type`  |
| ------------------------- | --------------- |
| `decisions/`              | Decision Record |
| `design/`                 | Design Doc      |
| `exec-plans/`             | Execution Plan  |
| `references/`             | Reference       |
| everything else           | Guide           |

Hand-edit the generated header when the default is wrong; the helper never
rewrites existing frontmatter.

### Index files

An `index.md` enumerates a directory for progressive disclosure — an agent
reads the index before opening documents. OKF index body format:

```markdown
# Section Heading

* [Title 1](relative-url-1) - short description from frontmatter
* [Subdirectory](subdir/) - short description of the subdirectory
```

- Index files contain no frontmatter, with one exception: the bundle-root
  `index.md` may carry a frontmatter block declaring `okf_version: "0.1"`.
- This skill generates index entries between explicit markers so hand-written
  prose can surround the catalog:

```markdown
<!-- BEGIN GENERATED DOCS INDEX -->
…generated; never hand-edit…
<!-- END GENERATED DOCS INDEX -->
```

### Gotchas

- Never start a frontmatter-free document body with a `---` horizontal rule:
  OKF parsers (including the reference implementation) read a leading `---`
  as an unterminated frontmatter opener and reject the file. Use `***` for a
  horizontal rule or add real frontmatter.
- Vendored and hidden directories (`node_modules`, `vendor`, dot-folders, …)
  are excluded from scanning; the `check` summary lists what was skipped so
  the exclusion is visible, not silent.

### Links, logs, citations

- Prefer bundle-relative links (`/decisions/adr-0001.md`) or plain relative
  links; a link asserts a relationship between concepts.
- Broken links are reported by validation but are not fatal to consumers —
  they may represent not-yet-written knowledge.
- An optional `log.md` records history, newest first, grouped under ISO
  `## YYYY-MM-DD` headings.
- Claims sourced from external material get a numbered `# Citations` section
  at the bottom of the body.

### Conformance checklist (OKF §9)

A bundle conforms when:

1. Every non-reserved `.md` file has a parseable YAML frontmatter block.
2. Every frontmatter block has a non-empty `type`.
3. `index.md` / `log.md` files follow their structural formats when present.

Everything else is soft guidance; consumers must not reject bundles over
missing optional fields or unknown types.

## Helper Script

All deterministic work goes through `scripts/easy_docs.py` inside this
skill's directory (the folder containing this `SKILL.md`); resolve it from
there regardless of where the skill is installed. It is idempotent and prints
a stable JSON summary to stdout; diagnostics go to stderr.

```sh
uv run --script <skill-dir>/scripts/easy_docs.py <command> --root /path/to/repo
```

Commands (default bundle is `<root>/docs`; override with `--bundle <dir>`):

- `scaffold` — create the missing docs system files: `docs/index.md` (with
  `okf_version` frontmatter and generated markers), core guide stubs with OKF
  headers (`architecture`, `repo-standards`, `local-development`, `testing`,
  `validation-loop`, `observability`, `security`, `reliability`,
  `release-process`, `pr-review-workflow`, `merge-policy`,
  `cleanup-workflow`, `engineering-maintenance`), specialized folders
  (`decisions/`, `design/`, `exec-plans/`, `references/`) each with a
  marker-bearing `index.md`, `references/docs-maintenance.md`, and
  `references/entrypoint-readme-template.md`. Existing files are never
  touched.
- `headers` — add OKF frontmatter where missing (`--check` only reports;
  `--write` edits). `type` comes from the taxonomy above, `title` from the
  first `#` heading (falling back to the filename), `description` from the
  first prose paragraph when one exists, `timestamp` from the file's last git
  commit date (falling back to `--default-date`, only in `--write` mode).
  Existing frontmatter is never modified.
- `index` — regenerate (`--write`) or drift-check (`--check`) every generated
  catalog region in the bundle: one per directory `index.md`, grouped by
  `type`, entries sorted by title, descriptions pulled from frontmatter. If
  `AGENTS.md` at the repo root contains `<!-- BEGIN GENERATED CORE DOCS -->`
  / `<!-- END GENERATED CORE DOCS -->` markers, the core docs list is
  maintained there too.
- `check` — the full validation gate: OKF conformance (frontmatter parses,
  `type` is a non-empty string, only the bundle-root index carries
  frontmatter), index drift, malformed generated-marker blocks, broken
  internal links, the 500-line rule for root `docs/*.md`, `index.md` presence
  in folders that contain docs, and `log.md` heading format (real ISO dates,
  newest first). Exit code 0 only when no errors remain; the summary lists
  directories skipped by the vendored/hidden-directory filter so nothing is
  silently out of scope.

`--check` never writes, never creates directories, and never depends on the
current time, so it is safe for CI and pre-commit hooks. A missing root or
bundle directory is an explicit failure (exit 2), not a silent pass, and
symlinked markdown files are never followed or rewritten.

## Required Workflow

1. Inspect the repository before writing: locate the docs tree (or its
   absence), existing indexes, and any generated markers.
2. Run `scaffold` when docs system files are missing. Immediately fill any
   stub the conversation already has content for — if the user described the
   system, write `docs/architecture.md` instead of leaving a placeholder.
3. Run `headers --write`, then review the generated frontmatter: fix wrong
   `type` values and sharpen weak descriptions — they become the index text.
4. Run `index --write` to build every catalog, then `check` and fix whatever
   it reports until it exits 0.
5. Wire `check` into the repository's validation loop (a `just` recipe,
   pre-commit hook, or CI step) so index drift fails fast. Suggested recipe:

   ```just
   docs-check:
       uv run --script <skill-dir>/scripts/easy_docs.py check --root .
   ```

6. Report remaining `PLACE HOLDER` markers to the user as the documentation
   backlog before finishing.

Never restructure an existing docs tree without explaining the moves first:
map current files, show the target layout, and get agreement before moving
anything.

## Composing With repository-bootstrap

The `repository-bootstrap` skill owns repository *structure* (target central
folders, `AGENTS.md`, tooling templates, adoption plans) and creates only a
minimal `docs/index.md` stub. This skill owns everything inside the docs
system. When bootstrapping a new repository, run `repository-bootstrap`
first, then this skill's `scaffold` + `headers --write` + `index --write` to
build the docs tree and populate the `GENERATED CORE DOCS` block that the
bootstrap `AGENTS.md` template carries.

## Definition Of Done

- Every non-reserved doc in the bundle has conformant OKF frontmatter.
- Every directory index and the `AGENTS.md` core docs block are generated,
  current, and pass `index --check`.
- `check` exits 0, or every remaining failure is reported to the user with a
  reason.
- Docs-system rules (500-line limit, specialized `index.md` files,
  docs-maintenance ownership) hold.
- The skill's own `just test` passes after changes to this skill.
