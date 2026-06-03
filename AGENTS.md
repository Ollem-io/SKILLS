# SKILLS Agent Guide

This is the short repo map for agents. Use [docs/index.md](docs/index.md) for
the full documentation table of contents.

## Repository Map

- [readme.md](readme.md) describes the public purpose and skill contract.
- [project.md](project.md) owns the repository specification.
- [skills/](skills/) contains one self-contained Codex skill per folder.
- [scripts/](scripts/) contains repository-level validation helpers.
- [.github/workflows/](.github/workflows/) contains CI validation workflows.

## Target Entrypoints

- [repository-bootstrap](skills/repository-bootstrap/SKILL.md) scaffolds or
  adopts Codex-friendly repository structure.

## Core Docs

- [Architecture](docs/architecture.md)
- [Structure guide](docs/structure-guide.md)
- [Repo standards](docs/repo-standards.md)
- [Skill authoring](docs/skill-authoring/index.md)
- [Local development](docs/local-development.md)
- [Testing](docs/testing.md)
- [Validation loop](docs/validation-loop.md)
- [Observability](docs/observability.md)
- [Security](docs/security.md)
- [Reliability](docs/reliability.md)
- [Release process](docs/release-process.md)
- [PR review workflow](docs/pr-review-workflow.md)
- [Merge policy](docs/merge-policy.md)
- [Cleanup workflow](docs/cleanup-workflow.md)
- [Engineering maintenance](docs/engineering-maintenance.md)
- [Decision records](docs/decisions/index.md)
- [Execution plans](docs/exec-plans/index.md)
- [Documentation references](docs/references/index.md)
- [Agent Skills standard](docs/references/agent-skills-standard.md) — primary
  `SKILL.md` format reference
- [Docs maintenance](docs/references/docs-maintenance.md)

## Working Rules

- Keep each skill self-contained under `skills/<skill-name>/`.
- Update `AGENTS.md`, [docs/index.md](docs/index.md), and the relevant skill
  docs when adding, moving, or removing an entrypoint.
- Prefer deterministic scripts with tests over chat-only instructions.
- Run the narrowest useful validation before handing off changes.
