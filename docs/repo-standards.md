# Repo Standards

## Skills

- Every skill conforms to the
  [Agent Skills standard](references/agent-skills-standard.md), which owns the
  `SKILL.md` frontmatter contract (`name`, `description`, `license`,
  `compatibility`, `metadata`, `allowed-tools` and their limits).
- Follow [Skill authoring](skill-authoring/index.md) for instruction patterns,
  script design, descriptions, and evaluation.
- `scripts/validate_skill_names.py` enforces the frontmatter contract in CI:
  allowed-field whitelist, `name` (ASCII subset, <= 64 chars, matches the
  directory), `description` (non-empty, <= 1024 chars), and `compatibility`
  (<= 500 chars). It is a subset of the upstream `skills-ref` validator and does
  not yet check unicode names or full `metadata` value typing.

## Repository Layout

- `AGENTS.md` is the short map for agents.
- `docs/index.md` is the full documentation table of contents.
- `project.md` contains the product or repository specification.
- Target-specific folders must follow [Structure Guide](structure-guide.md).

## Documentation

- Documentation must flow `docs/` -> topic file -> topic folder when needed.
- Any `.md` file directly under `docs/` must stay at or below 500 lines.
- If a root `docs/*.md` topic grows too large, create a folder with the same
  base name and move detailed content there.
- Every specialized documentation folder must include an `index.md`.
- Update `AGENTS.md` and `docs/index.md` in the same change as new entrypoints.

## Tooling

- Prefer repo-local task runners over chat-only instructions.
- Use `just` for repeatable commands when available.
- Use `mise` for tool installation and task encapsulation when available.
- Follow all configured pre-commit validations.

## Language Standards

| Language | Package manager | Type checker | Linter |
| --- | --- | --- | --- |
| Python | `uv` | `ty` | `ruff` |
| TypeScript | `vp` | `vp` (`tsgo`) | `vp` (`oxlint`) |

## Scripts And Tests

- Scripts must be deterministic for the same input.
- Scripts with side effects must be safe to run repeatedly.
- Every helper script should have a test.
- Expose the narrowest useful validation command for each target folder.

## Commits

- Use Conventional Commit messages: `type(scope): description`.
- Keep descriptions concise, lowercase, and without a trailing period.
