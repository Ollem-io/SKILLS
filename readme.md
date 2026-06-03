# SKILLS

Repository of the public skills of the Ollem.io project. This repository contains that are being developed and maintained through the dogfooding process. Feel free to use them as a reference for your own skills. Or to contribute to the project.

## Layout

- [AGENTS.md](AGENTS.md) - agent entrypoint and must-follow rules.
- [docs/](docs/index.md) - repository standards and local development guidance.
- `skills/<skill-name>/` - one self-contained Codex skill per folder.

Current skills:

- [repository-bootstrap](skills/repository-bootstrap/SKILL.md) - scaffold or
  adopt AI-agent-friendly repository structure (Codex, Claude Code, Cursor, and
  other agents) for monorepo, site, sites, custom, import, and adopt targets.

## Skill Contract

Each skill must include:

- `SKILL.md` as the source of truth.
- `Justfile` with a `test` command.
- tests for every helper script.
- deterministic scripts that produce the same output for the same input.
- related documentation updates when a skill is added or changed.

Supported helper script runtimes:

- Python with `uv`, `ty`, and `ruff`.
- TypeScript with `vp`, which runs `tsgo` and `oxlint`.

## Validation

Run tests from the relevant skill directory:

```sh
cd skills/<skill-name>
just test
```

For repository-wide rules, see [docs/repo-standards.md](docs/repo-standards.md)
and [docs/structure-guide.md](docs/structure-guide.md).
