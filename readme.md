# SKILLS

Public repository of agent **skills** maintained by the Ollem.io project. Each
skill is a self-contained capability that AI coding agents (Claude Code, Cursor,
Codex, and others) can load to perform a class of tasks. They are built and
hardened through dogfooding, then published for reuse. Use them as a reference
for your own skills, or contribute to the project.

## Install

Skills are distributed through [skills.sh](docs/references/skills-sh.md).
Install this repository's skills into your agent with:

```sh
npx skills add Ollem-io/SKILLS
```

Each published skill is covered by the skills.sh automated security audits.

## Layout

- [AGENTS.md](AGENTS.md) - agent entrypoint and must-follow rules.
- [docs/](docs/index.md) - repository standards and local development guidance.
- `skills/<skill-name>/` - one self-contained skill per folder.

Current skills:

- [repository-bootstrap](skills/repository-bootstrap/SKILL.md) - scaffold or
  adopt AI-agent-friendly repository structure (Codex, Claude Code, Cursor, and
  other agents) for monorepo, site, sites, custom, import, and adopt targets.
- [easy-docs](skills/easy-docs/SKILL.md) - organize repository documentation
  as an OKF (Open Knowledge Format) knowledge bundle: frontmatter headers,
  generated indexes, and a deterministic conformance check.

## Skill Contract

Each skill must include:

- `SKILL.md` as the source of truth, with valid frontmatter (`name`,
  `description`, and `compatibility`).
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

Validate every skill against the Agent Skills standard (uses the upstream
reference validator):

```sh
just validate-skill-spec
```

For repository-wide rules, see [docs/repo-standards.md](docs/repo-standards.md)
and [docs/structure-guide.md](docs/structure-guide.md). New skills follow the
[Release process](docs/release-process.md).
