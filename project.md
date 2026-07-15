# Project Specification

## Purpose

`Ollem-io/SKILLS` is the public repository of agent **skills** maintained by the
Ollem.io project. Each skill is a self-contained capability that any compatible
AI coding agent (Claude Code, Cursor, Codex, and others) can load to perform a
class of tasks. Skills are developed and hardened through dogfooding on Ollem.io
work, then published for reuse.

## Standard And Distribution

- Every skill conforms to the
  [Agent Skills standard](docs/references/agent-skills-standard.md)
  (agentskills.io). The standard owns the `SKILL.md` format.
- Distribution and discovery run through
  [skills.sh](docs/references/skills-sh.md): consumers install with
  `npx skills add Ollem-io/SKILLS`, and skills.sh runs automated security audits
  on each published skill.
- No build or publish step is required. A standards-clean
  `skills/<skill-name>/` folder on `main` is installable as-is.

## Skill Contract

Each skill under `skills/<skill-name>/` must include:

- `SKILL.md` — the source of truth, with valid frontmatter (`name`,
  `description`, and `compatibility` declaring environment and tool needs).
- `Justfile` exposing a `test` recipe.
- Deterministic helper scripts (same input → same output, safe to re-run).
- A test for every helper script.
- Documentation updates (`AGENTS.md`, `docs/index.md`, relevant docs) in the
  same change when an entrypoint is added, moved, or removed.

Supported helper-script runtimes:

- Python with `uv`, `ty`, and `ruff`.
- TypeScript with `vp` (which runs `tsgo` and `oxlint`).

## Current Skills

- [repository-bootstrap](skills/repository-bootstrap/SKILL.md) — scaffold or
  adopt AI-agent-friendly repository structure for `monorepo`, `site`, `sites`,
  `custom`, `import`, and `adopt` targets.
- [easy-docs](skills/easy-docs/SKILL.md) — organize repository documentation
  as an OKF (Open Knowledge Format) knowledge bundle: frontmatter headers,
  generated drift-checked indexes, and a conformance gate. Composes with
  `repository-bootstrap`, which owns repository structure.

## Governance

New and changed skills land via pull request to `main`, gated by CI and at least
one maintainer approval. See [Release process](docs/release-process.md) for the
full lifecycle.
