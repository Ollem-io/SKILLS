---
name: repository-bootstrap
description: Bootstrap or adopt a repository structure for AI-agent-friendly projects (Codex, Claude Code, Cursor, and other agents). Use when the user asks to create AGENTS.md, docs, repo standards, or a target layout for monorepo, site, sites, custom, import, or adopt repository setup.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
metadata:
  version: 0.4.0
  argument-hint: <target> [name/domain/custom folder]
  authors:
    - name: Davi Mello
      email: dsmello@ollem.io
---

# Repository Bootstrap

Create or adopt a repository structure with agent entrypoints, documentation
indexes, and target-specific source folders.

## Target Selection

- `monorepo` - use `components/` as the central folder. It contains multiple
  applications used together, such as frontend, backend, workers, and jobs.
- `site` - use `site/` as the central folder for a single website.
- `sites` - use `sites/` as the central folder for multiple websites. Prefer
  the website main domain as the site folder name, normalized with hyphens
  such as `ollem-io` for `ollem.io`.
- `custom` - follow the user's requested central folder and project rules.
- `import` or `adopt` - inspect the existing repository first and explain what
  must change to create an `AGENTS.md`, add the docs structure, or migrate
  files into the target pattern.

If a `sites` project has multiple versions for different targets, such as a
mobile version, ask the user for the preferred naming pattern before creating
folders. Suggested options are `m-ollem-io` or `ollem-io.mobile`.

## Required Workflow

1. Inspect the repository before writing files.
2. Choose the target from the user request. If the target is ambiguous, ask one
   concise question.
3. For `import` or `adopt`, do not immediately restructure files. Map the
   current repo, identify gaps, and explain what needs to change.
4. For `import` or `adopt`, classify candidate entrypoints by marker files such
   as `package.json`, `go.mod`, `pyproject.toml`, `Justfile`, `mise.toml`, and
   `Dockerfile`; report missing readmes, missing docs, stale links, and
   migration questions before changing structure.
5. For new scaffolds, create the complete docs and validation structure by
   default.
6. Put `PLACE HOLDER` only where project-specific content is still unknown.
7. Ensure `AGENTS.md` links to every created docs entrypoint.
8. Create `docs/references/docs-maintenance.md` with maintenance instructions
   for which file owns what and how to update indexes and `AGENTS.md`.
9. Enforce the destination repo's rules before delivery. At minimum, document
   deterministic scripts, script tests, `just test`, supported runtimes, secret
   handling, and Conventional Commit usage.

## Default Scaffold

The scaffold should follow the mature repository pattern:

- `AGENTS.md` is a short repo map, not a manual.
- `docs/index.md` is the complete documentation table of contents.
- root `docs/*.md` files stay below 500 lines and split into
  `docs/<topic>/index.md` when they grow.
- target entrypoint sections are named by target:
  - `Component Entrypoints` for `monorepo`
  - `App Entrypoint` for `site`
  - `Site Entrypoints` for `sites`
  - `Target Entrypoints` for `custom`
- major entrypoints should have readmes covering purpose, runtime surface,
  setup, commands, architecture notes, tests, environment variables, external
  dependencies, and Definition of Done.
- validation templates should include `Justfile`, `mise.toml`, `prek.toml`,
  Python `uv run --script` helpers, and minimal CI workflow placeholders.

## Scaffold Script

Use the deterministic scaffold helper when creating files:

```sh
uv run --script skills/repository-bootstrap/scripts/scaffold_repository.py \
  --root /path/to/repo \
  --target monorepo \
  --project-name example
```

Targets:

- `--target monorepo`
- `--target site`
- `--target sites --project-name ollem.io`
- `--target custom --central-folder apps`
- `--target adopt`
- `--target import`

The script is idempotent: it only creates missing files and directories, keeps
existing files intact, and prints a stable JSON summary.

## Definition Of Done

- The repository has `AGENTS.md`, the default `docs/` structure, and validation
  templates.
- The target central folder exists or the adoption plan explains why changes
  were not applied.
- `docs/references/docs-maintenance.md` explains documentation ownership and
  index update rules.
- New files are linked from `AGENTS.md` and `docs/index.md`.
- The skill's `just test` passes after changes to this skill.
