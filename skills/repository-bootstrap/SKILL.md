---
name: repository-bootstrap
description: Bootstrap, scaffold, or adopt a repository structure for AI-agent-friendly projects (Codex, Claude Code, Cursor, and other agents). Use when the user asks to create or initialize AGENTS.md, docs, repo standards, a project layout, directory structure, project template, or boilerplate; to set up a new repo or monorepo; to lay out a site, sites, or custom central folder; or to import or adopt an existing repository into the standard structure.
compatibility: Works with Claude Code, Cursor, Codex, and other Agent Skills clients. Needs the Bash, Read, Write, Edit, Glob, and Grep tools and write access to the target repository root. The scaffold helper requires `uv` (Python >= 3.11); running the skill's own tests additionally requires `just`. No network access.
allowed-tools: Bash Read Write Edit Glob Grep
license: GPL-3.0-or-later
metadata:
  version: "0.6.0"
  argument-hint: <target> [name/domain/custom folder]
  author: Davi Mello <dsmello@ollem.io>
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
  files into the target pattern. The two names are equivalent aliases for the
  same behavior.

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
7. After scaffolding, immediately fill what the conversation already knows:
   if the user described the project, write `project.md` and the
   `docs/architecture.md` system shape from that description instead of
   leaving placeholders; for a monorepo, fill the Component Map table in
   `docs/component-guide.md` with the planned components. Run the scaffold
   BEFORE authoring design docs so they land inside the final structure.
8. Ensure `AGENTS.md` links to every created docs entrypoint.
9. Create `docs/references/docs-maintenance.md` with maintenance instructions
   for which file owns what and how to update indexes and `AGENTS.md`.
10. Enforce the destination repo's rules before delivery. At minimum, document
    deterministic scripts, script tests, `just test`, supported runtimes,
    secret handling, and Conventional Commit usage.
11. Before delivery, list the remaining `PLACE HOLDER` markers
    (`grep -rn "PLACE HOLDER" docs/ project.md`) and report them to the user
    as the documentation backlog.

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
- `docs/decisions/index.md` documents the decision-record format (status,
  date, decision, rationale, consequences) and every record is linked from
  that index.
- `docs/design/index.md` hosts detailed designs (domain models, protocols,
  component internals) so `docs/architecture.md` stays a short system map.
- monorepo `docs/component-guide.md` carries a Component Map table
  (folder, language, purpose, tracker component value) that automation such
  as issue boards and agent pipelines can treat as canonical.
- root hygiene files are created by default: `readme.md`, `.gitignore`, and
  `.github/dependabot.yml`. Note: dependabot starts opening dependency PRs
  within hours of the first push — expected, but mention it to the user when
  other automation works the same repo.

## Scaffold Script

Use the deterministic scaffold helper when creating files. The script lives at
`scripts/scaffold_repository.py` inside this skill's own directory (the folder
containing this `SKILL.md`); resolve it from there regardless of where the
skill is installed:

```sh
uv run --script <skill-dir>/scripts/scaffold_repository.py \
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
