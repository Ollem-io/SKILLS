---
name: repository-bootstrap
description: Bootstrap, scaffold, or adopt repository structure for AI-agent-friendly projects (Codex, Claude Code, Cursor, and other agents). Use when the user asks to create or initialize AGENTS.md, docs, repo standards, a project layout, directory structure, project template, or boilerplate; to set up a new repo or monorepo; to lay out a site, sites, or custom central folder; or to import or adopt an existing repository into the standard structure.
compatibility: Works with Claude Code, Cursor, Codex, and other Agent Skills clients. Needs the Bash, Read, Write, Edit, Glob, and Grep tools and write access to the target repository root. The scaffold helper requires `uv` (Python >= 3.11); running the skill's own tests additionally requires `just`. No network access.
allowed-tools: Bash Read Write Edit Glob Grep
license: GPL-3.0-or-later
metadata:
  version: "0.7.0"
  argument-hint: <target> [name/domain/custom folder]
  author: Davi Mello <dsmello@ollem.io>
---

# Repository Bootstrap

Create or adopt repository structure with agent entrypoints, a minimal
documentation handoff, target-specific source folders, and validation tooling.

## Target Selection

- `monorepo` - use `components/` as the central folder. It contains multiple
  applications used together, such as frontend, backend, workers, and jobs.
- `site` - use `site/` as the central folder for a single website.
- `sites` - use `sites/` as the central folder for multiple websites. Prefer
  the website main domain as the site folder name, normalized with hyphens
  such as `ollem-io` for `ollem.io`.
- `custom` - follow the user's requested central folder and project rules.
- `import` or `adopt` - inspect the existing repository first and explain what
  must change to create an `AGENTS.md`, add the structural docs entrypoint, or
  migrate files into the target pattern. The two names are equivalent aliases
  for the same behavior.

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
   `Dockerfile`; report missing readmes, structural docs gaps, stale links, and
   migration questions before changing structure.
5. For new scaffolds, create `AGENTS.md`, `project.md`, a minimal
   `docs/index.md`, the target guide, the central folder, root hygiene files,
   and validation tooling.
6. Put `PLACE HOLDER` only where project-specific content is still unknown.
7. After scaffolding, immediately fill what the conversation already knows:
   if the user described the project, write `project.md`; for a monorepo, fill
   the Component Map table in `docs/component-guide.md` with the planned
   components.
8. Ensure `AGENTS.md` links every docs entrypoint this skill creates.
9. Recommend running the `easy-docs` skill after scaffolding to create and
   maintain the repository documentation system.
10. Enforce the destination repo's rules before delivery. At minimum, document
    deterministic scripts, script tests, `just test`, supported runtimes,
    secret handling, and Conventional Commit usage.
11. Before delivery, list the remaining `PLACE HOLDER` markers
    (`grep -rn "PLACE HOLDER" docs/ project.md`) and report them to the user as
    the documentation backlog.

## Default Scaffold

The scaffold follows this structural baseline:

- `AGENTS.md` is a short repo map, not a manual. It includes
  `GENERATED CORE DOCS` markers for `easy-docs` to populate.
- `project.md` is the repository or product specification placeholder.
- `docs/index.md` is a minimal OKF-aware stub with generated index markers.
- one target guide owns the central-folder contract:
  - `docs/component-guide.md` for `monorepo`
  - `docs/site-guide.md` for `site` and `sites`
  - `docs/structure-guide.md` for `custom`
- target entrypoint sections are named by target:
  - `Component Entrypoints` for `monorepo`
  - `App Entrypoint` for `site`
  - `Site Entrypoints` for `sites`
  - `Target Entrypoints` for `custom`
- monorepo `docs/component-guide.md` carries a Component Map table (folder,
  language, purpose, tracker component value) that automation such as issue
  boards and agent pipelines can treat as canonical.
- validation templates include `Justfile`, `mise.toml`, `prek.toml`, Python
  `uv run --script` helpers, and minimal CI workflow placeholders.
- root hygiene files include `readme.md`, `.gitignore`, and
  `.github/dependabot.yml`. Dependabot starts opening dependency PRs within
  hours of the first push; mention that when other automation works in the
  same repository.

The documentation system is not owned by this skill. Core guide docs,
`decisions/`, `design/`, `exec-plans/`, `references/`, OKF headers, generated
indexes, and docs-maintenance rules belong to `easy-docs`.

## Composing With easy-docs

When bootstrapping a repository, run `repository-bootstrap` first so the target
folder, `AGENTS.md`, minimal `docs/index.md`, target guide, and tooling exist.
Then run the `easy-docs` workflow in this order:

1. `scaffold` to create missing core guide docs and specialized folders.
2. `headers --write` to add missing OKF frontmatter.
3. `index --write` to populate every generated docs index and the
   `GENERATED CORE DOCS` region in `AGENTS.md`.
4. `check` to verify headers, indexes, and documentation rules.

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

- The repository has `AGENTS.md`, `project.md`, the minimal docs handoff,
  target structure, and validation templates.
- The target central folder exists or the adoption plan explains why changes
  were not applied.
- `AGENTS.md` contains the `GENERATED CORE DOCS` markers so `easy-docs` can
  maintain the core docs list.
- `AGENTS.md` links `project.md`, `docs/index.md`, and the target guide;
  `docs/index.md` links the target guide and contains the generated index markers.
- The skill's `just test` passes after changes to this skill.
